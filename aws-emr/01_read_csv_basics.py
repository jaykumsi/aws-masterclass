"""
Lesson 1: SparkSession + reading CSV off floci S3.

Run inside the pyspark container (it already has the S3A endpoint/creds
wired up via spark-defaults.conf):
    docker exec -it aws-floci-pyspark-1 python3 work/code/pyspark-code/01_read_csv_basics.py

Or paste into a Jupyter cell at http://localhost:8888.
"""
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("01-read-csv-basics").getOrCreate()

emp = spark.read.csv(
    "s3a://landing-zone/extracted/04_many_small_csv_emp/csv/emp/",
    header=True,
    inferSchema=True,
)

print("Schema (inferSchema reads the data once just to guess types):")
emp.printSchema()

print(f"Row count: {emp.count()}")

print("Sample rows:")
emp.show(5)

# spark.stop()
