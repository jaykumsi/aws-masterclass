"""
Lesson 4: groupBy/agg -- your first shuffle.

Unlike lesson 3's narrow ops, grouping needs every row for the same
deptno to land on the same partition before it can be aggregated. Spark
has to redistribute (shuffle) data across the network to make that happen.
The .explain() output will show an Exchange (hashpartitioning) node --
that's the shuffle boundary, and it's also where a new Stage starts (see
lesson 7 for how that maps to the DAG).

While this is running, check:
  - http://localhost:4040 (live) -- Stages tab, look at Shuffle Read/Write bytes
  - http://localhost:18080 (history, after it finishes) -- same info, persisted
"""
from pyspark.sql.functions import avg, count

from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("04-groupby-aggregations").getOrCreate()

emp = spark.read.csv(
    "s3a://landing-zone/extracted/04_many_small_csv_emp/csv/emp/",
    header=True,
    inferSchema=True,
)

by_dept = emp.groupBy("deptno").agg(
    avg("sal").alias("avg_sal"),
    count("*").alias("num_employees"),
)

print("Physical plan (look for the Exchange/hashpartitioning node = shuffle):")
by_dept.explain()

print("Average salary and headcount per department:")
by_dept.orderBy("deptno").show()

spark.stop()
