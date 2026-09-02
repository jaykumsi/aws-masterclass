# Run commands

## Why not just `python3 script.py`
The `pyspark` container's plain `python3` doesn't have `pyspark` on its path --
only `spark-submit` (and the Jupyter kernel at localhost:8888) wire that up.
Running a lesson script with bare `python3` fails with
`ModuleNotFoundError: No module named 'pyspark'`.

## Start/update the stack
```
cd c:\code\aws-floci
docker compose up -d
docker compose ps
```

## Prep step (run once, on the host -- boto3, no Spark)
Needs boto3 + the `floci` AWS profile set up per README.md.
```
cd c:\code\aws-floci\code\pyspark-code
python 00_prep_extract_zips_to_s3.py
```

## Lesson scripts (run inside the pyspark container, via spark-submit)
```
docker exec -it aws-floci-pyspark-1 /usr/local/spark/bin/spark-submit /home/jovyan/work/code/pyspark-code/01_read_csv_basics.py
docker exec -it aws-floci-pyspark-1 /usr/local/spark/bin/spark-submit /home/jovyan/work/code/pyspark-code/02_read_json_and_parquet.py
docker exec -it aws-floci-pyspark-1 /usr/local/spark/bin/spark-submit /home/jovyan/work/code/pyspark-code/03_transformations.py
docker exec -it aws-floci-pyspark-1 /usr/local/spark/bin/spark-submit /home/jovyan/work/code/pyspark-code/04_groupby_aggregations.py
docker exec -it aws-floci-pyspark-1 /usr/local/spark/bin/spark-submit /home/jovyan/work/code/pyspark-code/05_joins.py
docker exec -it aws-floci-pyspark-1 /usr/local/spark/bin/spark-submit /home/jovyan/work/code/pyspark-code/06_write_target_files.py
```

## UIs
- Jupyter: http://localhost:8888 (token `floci`)
- Spark live UI: http://localhost:4040 -- only reachable while a SparkSession
  is actively running (e.g. mid-script, or a Jupyter cell that hasn't called
  `spark.stop()` yet). Goes dead as soon as the session ends.
- Spark history server: http://localhost:18080 -- shows completed sessions
  after they end (reads event logs from `data/spark-events/`).

## Running a lesson via python3 directly instead of spark-submit
Only needed if you want to `python3 script.py` inside the container instead
of `spark-submit`. Set `PYTHONPATH` first:
```
docker exec -it aws-floci-pyspark-1 bash -lc '
  export PYTHONPATH=$SPARK_HOME/python:$SPARK_HOME/python/lib/py4j-0.10.9.7-src.zip
  python3 /home/jovyan/work/code/pyspark-code/01_read_csv_basics.py
```
