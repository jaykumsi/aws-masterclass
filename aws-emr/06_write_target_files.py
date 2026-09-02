"""
Lesson 6: writing target files -- output file count is a choice, not an accident.

We build a small "budget per department" summary (join + groupBy from
lessons 4/5) and write it out three ways, to make output file count
concrete:
  1. default -- one file per output partition (however many that is)
  2. .coalesce(1) -- merge down to a single output file
  3. .partitionBy("deptno") -- one subfolder per department, Hive-style

Check the object counts in floci (e.g. via floci_s3_bucket_operations.list_objects)
to see the difference land as real S3 keys.
"""
from pyspark.sql.functions import sum as sum_

from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("06-write-target-files").getOrCreate()

base = "s3a://landing-zone/extracted/05_many_small_csv_multiple_tables/csv"


def read_table(name):
    return spark.read.csv(f"{base}/{name}/", header=True, inferSchema=True)


emp = read_table("emp")
dept = read_table("dept")
emp_projects = read_table("emp_projects")
projects = read_table("projects")

budget_per_dept = (
    emp.join(dept, on="deptno")
    .join(emp_projects, on="empno")
    .join(projects, on="project_id")
    .groupBy("deptno", "dname")
    .agg(sum_("budget").alias("total_project_budget"))
)

print(f"Output partitions before writing: {budget_per_dept.rdd.getNumPartitions()}")
budget_per_dept.show()

out_base = "s3a://landing-zone/targets/budget_per_dept"

# NB: on this tiny local dataset, Adaptive Query Execution already
# coalesces everything down to 1 partition on its own -- so an
# un-repartitioned write would produce 1 file anyway and the comparison
# below would be a no-op. repartition(4) forces a visible "before" state
# so coalesce(1) has something real to collapse. On real, larger data you
# wouldn't repartition(4) by hand -- the partition count would already
# reflect spark.sql.shuffle.partitions / AQE's own coalescing.
budget_per_dept.repartition(4).write.mode("overwrite").parquet(f"{out_base}/many_files")
budget_per_dept.coalesce(1).write.mode("overwrite").parquet(f"{out_base}/single_file")
budget_per_dept.write.mode("overwrite").partitionBy("deptno").parquet(f"{out_base}/by_dept")

print("Wrote 3 variants under targets/budget_per_dept/ -- compare object counts:")
print(f"  {out_base}/many_files/    (repartition(4) -> up to 4 files)")
print(f"  {out_base}/single_file/   (coalesce(1) -> 1 file)")
print(f"  {out_base}/by_dept/       (partitionBy -> 1 subfolder per deptno)")

readback = spark.read.parquet(f"{out_base}/single_file")
print(f"Read-back row count: {readback.count()}")

spark.stop()
