"""
Lesson 2: same emp table, three formats, three different reader behaviors.

CSV/JSON are schema-on-read (Spark scans the data to guess types).
Parquet carries its own schema in the file footer, so reading it is cheap
and the types are exact -- no guessing pass needed.
"""
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("02-read-json-and-parquet").getOrCreate()

base = "s3a://landing-zone/extracted/04_many_small_csv_emp"

print("=== JSON (schema inferred by scanning the data) ===")
emp_json = spark.read.json(f"{base}/json/emp/")
emp_json.printSchema()
emp_json.show(3)

print("=== Parquet (schema read from the file footer, no scan needed) ===")
# NB: reading the whole parquet/emp/ folder currently blows up -- one of
# the 20 part-files stores "mgr" with a different physical type (INT64)
# than the rest (INT32), and Spark's parquet reader locks in its schema
# from the first file it opens. That's a genuine schema-drift bug baked
# into this dataset; we'll deal with reconciling it head-on in the
# many-small-files / schema-evolution lesson. For now, read one file so
# the format comparison itself isn't blocked by it.
emp_parquet = spark.read.parquet(f"{base}/parquet/emp/part_0000001.parquet")
emp_parquet.printSchema()
emp_parquet.show(3)

print(f"json rows: {emp_json.count()}, parquet rows (1 file only): {emp_parquet.count()}")

spark.stop()
