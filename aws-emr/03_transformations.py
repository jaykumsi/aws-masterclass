"""
Lesson 3: narrow transformations -- select/filter/withColumn.

"Narrow" means each output partition depends on exactly one input
partition: no data has to move between executors. select/filter/withColumn
are all narrow. Nothing runs yet -- transformations are lazy, they just
build up the plan. The .explain() at the bottom shows a single stage with
no Exchange (shuffle) node, which is what "narrow" looks like in a plan.
"""
from pyspark.sql.functions import col

from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("03-transformations").getOrCreate()

emp = spark.read.csv(
    "s3a://landing-zone/extracted/04_many_small_csv_emp/csv/emp/",
    header=True,
    inferSchema=True,
)

result = (
    emp.select("empno", "ename", "job", "sal", "deptno")
    .filter(col("job") == "analyst")
    .withColumn("annual_sal", col("sal") * 12)
)

print("Analysts with annual salary:")
result.show(10)

print("Physical plan (look for the absence of an Exchange node):")
result.explain()

spark.stop()
