# Understanding Event Log in Spark UI

## Glossary: App > DAG > Job > Stage > Task
* **App** — one Spark script/session, start to finish (`spark-submit script.py`, or one Jupyter kernel). Everything below happens inside one App.
* **DAG** — the full plan for a query, built lazily as you chain `.select()`/`.filter()`/`.groupBy()` etc. Nothing runs until an *action* (`.show()`, `.count()`, `.write()`) triggers it.
* **Job** — created every time an action runs. One App/DAG can trigger many Jobs (e.g. `inferSchema=True` on read is itself a Job, before your `.show()` runs a second one).
* **Stage** — a Job is split into Stages at every point data has to move between executors (a **shuffle**) — `.groupBy()`, `.join()` (non-broadcast), `.repartition()`. Narrow ops (`select`/`filter`/`withColumn`) stay inside one Stage.
* **Task** — a Stage split into the smallest unit of work: one Task per input partition, all running the same code on a different slice of data.

This doc is about where all five of those actually show up on disk and in the UI — the **event log**.

## Step 1: Run a script that has a shuffle in it
`04_groupby_aggregations.py` is the one to use here — its `.groupBy("deptno")` forces a shuffle, so it produces a Job with more than one Stage, which is what makes the event log interesting to read.
```
docker exec -it aws-floci-pyspark-1 /usr/local/spark/bin/spark-submit /home/jovyan/work/code/pyspark-code/04_groupby_aggregations.py
```

## Step 2: Where the event log actually lives
`spark-defaults.conf` (repo root) turns this on for every script in this project:
```
spark.eventLog.enabled true
spark.eventLog.dir file:/home/jovyan/work/spark-events
```
That path is a bind mount, so on the host it's `data\spark-events\`. Every run creates **one file per App**, named `local-<timestamp>` (a real cluster would name it `app-<timestamp>-<id>`):
```
data\spark-events\local-1786133633294
```
That single file *is* the entire event log the history server (`localhost:18080`) reads from. Nothing else backs that UI — if you delete the file, that run disappears from the history server's list.

> 📸 Screenshot: `screenshots/01-history-server-app-list.png` — the app list at localhost:18080, with the file you just ran highlighted.

## Step 3: What's actually in the file
It's **newline-delimited JSON** — one JSON object per line, one line per event, in the order they happened. No indentation, no wrapping array. You can read it directly:
```
docker exec -it aws-floci-pyspark-1 bash -lc "tail -f /home/jovyan/work/spark-events/local-<timestamp>"
```
or pull it apart with Python (this is exactly how the numbers in this doc were pulled):
```python
import json
events = [json.loads(line) for line in open("local-1786133633294")]
print(len(events), "events")
```

A typical run produces a predictable mix of event types. From the 04_groupby_aggregations.py run used for this doc (117 events total):

| Event | Count | What it marks |
|---|---|---|
| `SparkListenerApplicationStart` / `...End` | 1 / 1 | the App itself |
| `SparkListenerJobStart` / `...End` | 4 / 4 | one pair per Job (this script triggers 4 -- 2 for `inferSchema=True`'s own read pass, 2 for the actual `groupBy`/`show`; see Step 4) |
| `SparkListenerStageSubmitted` / `...Completed` | 4 / 4 | one pair per Stage that *actually ran*. 5 distinct Stage IDs show up across the 4 Jobs (0,1,2,3,4), but Stage 3 never gets a Submitted/Completed pair -- it was skipped (Step 4) |
| `SparkListenerTaskStart` / `...End` | 42 / 42 | one pair per Task across all Stages |
| `SparkListenerSQLExecutionStart` / `...End` | 2 / 2 | DataFrame/SQL-level query tracking (separate from the RDD-level Job/Stage/Task events above) |
| `SparkListenerExecutorAdded`, `BlockManagerAdded`, `EnvironmentUpdate`, `ResourceProfileAdded`, `LogStart` | 1 each | one-time setup events at the start of the App |

## Step 4: Reading one Job in detail — where the Stage split shows up
This is the concrete payoff: proving the DAG → Job → Stage → Task hierarchy from the glossary against real event data, not just the UI's visualization of it. Don't guess at this from the UI alone — pull `Stage Infos` out of every `SparkListenerJobStart` event and you get the ground truth:
```
Job 0 -> stage 0  (1 task)   -- cheap first pass over the csv (schema bootstrap)
Job 1 -> stage 1  (20 tasks) -- inferSchema=True's real cost: a full scan of every
                                 row in every one of the 20 part-files to work out
                                 column types, *before* your groupBy ever runs
Job 2 -> stage 2  (20 tasks) -- the actual groupBy("deptno") map-side: re-scans the
                                 csv, partially aggregates per partition, shuffle-writes
Job 3 -> stage 3  (skipped!) and stage 4 (1 task) -- see below
```
Two things worth slowing down on:

**inferSchema is not free.** Jobs 0 and 1 exist purely because `spark.read.csv(..., inferSchema=True)` has to read the data once just to guess types, *before* anything you actually asked for (the groupBy) runs at all. In production you'd usually pass an explicit `schema=` to skip this pass entirely — this event log is the receipt for why that optimization matters.

**Job 3's Stage 3 never actually ran.** There's no `SparkListenerStageSubmitted`/`...Completed` pair for Stage 3 anywhere in the log — Spark's Adaptive Query Execution (AQE, on by default since Spark 3.x) had already materialized that exact shuffle output while running Job 2, so it reused it instead of recomputing it. This is exactly what the Spark UI's Stages page calls a **"Skipped Stage"** (shown greyed out) — one of the most confusing things in the UI if you don't know why it happens. The lesson: **Job 2's Stage 2 is the real map-side of the shuffle** (scan → partial aggregate → shuffle write), and **Job 3's Stage 4 is the reduce side** (shuffle read → final aggregate → sort for `orderBy` → collect for `show()`). AQE splits the query into more Jobs than the classic "one Job per action" mental model suggests, specifically so it can materialize each shuffle boundary and use the real (not estimated) output size to plan the next step.

> 📸 Screenshot: `screenshots/02-jobs-tab-all-4-jobs.png` — the Jobs tab, all 4 Jobs listed, Job 3 expanded.
>
> 📸 Screenshot: `screenshots/03-job3-dag-visualization.png` — Job 3's "DAG Visualization" (click into the job) — Stage 3 should appear greyed out / labeled "skipped".

## Step 5: Reading shuffle metrics on individual tasks — proving data actually moved
Every `SparkListenerTaskEnd` event carries a `Task Metrics` block. Summed across all 20 tasks in each stage:

**Stage 2 (map side — writes shuffle data):**
```
Stage 2 shuffle write total: 12584 bytes, 200 records
```
**Stage 4 (reduce side — reads shuffle data, 1 task since AQE coalesced the post-shuffle partitions down to 1 for this small dataset):**
```
Stage 4 shuffle read total: 12584 bytes, 200 records
```
Bytes and record counts match exactly between the write side and the read side, which is the event log proving the shuffle actually moved *all* the data, not a sample — every one of the emp table's 200 rows had to cross the shuffle boundary to be grouped by `deptno`. On a dataset too big to fit comfortably in memory, this Shuffle Read/Write pair is exactly what you'd watch to catch a shuffle that's disproportionately expensive relative to the data volume.

> 📸 Screenshot: `screenshots/04-stage2-task-table.png` — the Stage 2 detail page, task table, Shuffle Write Size/Records column visible across all 20 tasks.
>
> 📸 Screenshot: `screenshots/05-stage4-task-table.png` — the Stage 4 detail page — 1 task, Shuffle Read Size/Records matching Stage 2's write total.
>
> 📸 Screenshot: `screenshots/06-stage-summary-metrics.png` — the Stage summary block at the top of either page (min/median/max per task) — this is where you'd spot skew: one task reading far more than the median is the signature of a skewed key.

## Step 6: All action types — what actually triggers a Job
Everything in the glossary's DAG bullet only fires once you call an **action**. Transformations (`select`, `filter`, `withColumn`, `groupBy`, `join`, ...) just extend the plan; nothing runs, nothing shows up in the event log, until one of these is called:

| Action | Notes |
|---|---|
| `.show()` | what every lesson script so far uses |
| `.collect()` | pulls **every** row to the driver — the one most likely to OOM the driver on real data |
| `.count()` | |
| `.take(n)` / `.head(n)` / `.first()` | often cheaper than `.collect()` — Spark can stop early once it has enough rows |
| `.toPandas()` | collects to the driver, then converts — same blast radius as `.collect()` |
| `.write.parquet(...)` / `.csv(...)` / `.json(...)` / `.saveAsTable(...)` / `.jdbc(...)` | lesson 6 |
| `.foreach(...)` / `.foreachPartition(...)` | runs a function per row/partition for side effects, returns nothing to the driver |
| `.reduce(...)` (RDD-level) | |

**Traps — things that look like actions but aren't:**
* `.explain()` — prints the plan text only. We confirmed this directly: every `.explain()` in these lessons prints `AdaptiveSparkPlan isFinalPlan=false`, meaning AQE hasn't executed anything yet. No Job, no event log entries.
* `.printSchema()` — metadata only. For an explicit `schema=...` this is free; for `inferSchema=True` the schema was already computed by the read-time inference Job (Step 4), so this is just printing something already known.
* `.cache()` / `.persist()` — lazy, same as any transformation. It marks the DataFrame for caching but doesn't actually compute or cache anything until the *next* action runs.

## Step 7: All shuffle-triggering operations
Verified directly against this project's emp table by checking `df._jdf.queryExecution().executedPlan().toString()` for an `Exchange` node (not just recited from docs):

| Operation | Shuffles? |
|---|---|
| `.groupBy(...).agg(...)` | Yes (Step 4/5) |
| `.join(...)` (non-broadcast side) | Yes (`05_joins.py`) |
| `.distinct()` | Yes -- confirmed |
| `.dropDuplicates([...])` | Yes -- confirmed |
| `.orderBy(...)` / `.sort(...)` | Yes -- confirmed, **even with no groupBy before it**. Getting a global order means every row has to be comparable against every other row, which needs a range-partitioning shuffle |
| `.repartition(n)` / `.repartition(n, col)` | Yes -- confirmed. This is the one that shuffles *on purpose*, purely to change partition count/layout |
| `Window.partitionBy(...)` | Yes -- confirmed. Same idea as groupBy: rows sharing a window key have to land together |
| `.reduceByKey(...)` / `.aggregateByKey(...)` / `.groupByKey(...)` / `.cogroup(...)` (RDD-level) | Yes (not re-tested here, but the same key-redistribution logic as groupBy) |
| `.intersect(...)` / `.subtract(...)` / `.exceptAll(...)` | Yes (set operations need matching rows on the same partition) |
| `.select(...)` / `.filter(...)` / `.withColumn(...)` | No -- confirmed narrow (Step 3 lesson) |
| `.union(...)` | No -- confirmed. Just stacks partitions, no key redistribution |
| `.coalesce(n)` | No -- confirmed, **this is the opposite of repartition**: it only ever merges existing partitions on the same executor, never moves data across the network. That's exactly why `06_write_target_files.py` uses `.coalesce(1)` to merge to one file cheaply, and `.repartition(4)` (a real shuffle) to fan back out |

## Step 8: Do shuffles only show up as a Stage split, or elsewhere too?
Elsewhere too — the Stage split is just the most visible one. Four distinct places carry shuffle evidence, and they come from **different event types**, not one:

1. **The plan structure itself** (`.explain()`, or the Stages/SQL tab's static plan) — shows *that* an Exchange exists, before anything has run. No numbers yet, just structure.
2. **The Stages page / Task Metrics** — what Steps 4-5 of this doc used. Each `SparkListenerTaskEnd` event carries `Shuffle Read Metrics`/`Shuffle Write Metrics`. The Stage boundary itself *is* the shuffle boundary — this is the "Stage split" view.
3. **The SQL tab's plan diagram** — a *second, independent* set of numbers, sourced from a different event entirely. We confirmed this directly: the `Exchange` node in `sparkPlanInfo` (from `SparkListenerSQLExecutionStart`) owns its own named metrics —  `shuffle bytes written`, `shuffle records written`, `data size`, `number of partitions` — each tied to an accumulator ID (127-146 in our run). The actual values arrive later via `SparkListenerDriverAccumUpdates` (`accumUpdates: [[id, value], ...]`), which is what lets the SQL tab annotate the Exchange box with real numbers after execution, separate from anything on the Stages page.
4. **The Executors page** — the same Task Metrics from #2, but summed by executor instead of by stage. Not a new event type, just a different aggregation. In this project's local, single-executor setup this column is uninteresting (everything lands on the one executor) — it only becomes useful on a real multi-executor cluster, where it's how you'd spot one executor doing disproportionately more shuffle work than the others.

So: the Stage split tells you *where* the shuffle boundary is; the Task Metrics on that Stage tell you the shuffle cost from the RDD side; the SQL tab's Exchange node tells you the same cost again from the query-plan side, independently computed. On a real performance problem, checking both #2 and #3 agree is a good sanity check — if the Stages page shows a huge shuffle but the SQL tab's Exchange node claims a tiny `data size`, that's a sign of a `data size` vs actual bytes-on-the-wire discrepancy worth digging into (compression, or the estimate AQE used to make a broadcast/sort-merge decision being wrong).

> 📸 Screenshot: `screenshots/07-sql-tab-exchange-node.png` — the SQL tab, this query's plan diagram, Exchange box expanded showing its own shuffle metrics.
>
> 📸 Screenshot: `screenshots/08-executors-tab-shuffle-columns.png` — the Executors page, Shuffle Read/Write columns (even though there's only one row locally, worth having for comparison against a real cluster later).

## What's next
This doc covers Job/Stage/Task, every action type, every shuffle-triggering op, and all four places shuffle evidence shows up, using a clean, non-skewed example. Natural follow-ups, once you've got screenshots in for the above:
* A doc on **spotting skew** in the task table (uneven Shuffle Read Size across tasks in the same stage) using the large-sales dataset.
* A doc on the **many-small-files** dataset, where the interesting thing isn't the shuffle at all but the sheer *Task Start/End* event count from having thousands of tiny input partitions.
* A doc on **spill** (`Memory Bytes Spilled` / `Disk Bytes Spilled` in Task Metrics — seen but unused so far since nothing in these lessons has spilled) — what it looks like when a shuffle or aggregation doesn't fit in memory.
