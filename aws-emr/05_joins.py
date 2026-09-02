"""
Lesson 5: joins -- broadcast vs. shuffle.

emp/dept/emp_projects/projects is a classic star-ish schema:
  emp(empno, ..., deptno) --< emp_projects(empno, project_id) >-- projects(project_id, ...)
  emp(deptno) --< dept(deptno)

dept is tiny (a handful of rows), so Spark's planner broadcasts it to
every executor instead of shuffling both sides -- cheaper when one side
is small. emp_projects/projects are small too in this sample data (every
dataset here is small enough to fit under Spark's default 10MB broadcast
threshold), so left alone Spark broadcasts *both* joins. To actually see
the alternative -- a shuffle (sort-merge) join, where both sides get
redistributed by key -- we disable auto-broadcast for the second join.
On real, larger tables you'd rarely do this by hand; Spark's planner
would pick sort-merge on its own once both sides are too big to broadcast.
Compare the two explain() plans: one has BroadcastHashJoin +
BroadcastExchange, the other has SortMergeJoin + Exchange on both sides.
"""
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("05-joins").getOrCreate()

base = "s3a://landing-zone/extracted/05_many_small_csv_multiple_tables/csv"


def read_table(name):
    return spark.read.csv(f"{base}/{name}/", header=True, inferSchema=True)


emp = read_table("emp")
dept = read_table("dept")
emp_projects = read_table("emp_projects")
projects = read_table("projects")

print("=== emp JOIN dept (dept is small -> broadcast join) ===")
emp_dept = emp.join(dept, on="deptno", how="inner")
emp_dept.explain()
emp_dept.select("empno", "ename", "dname", "loc").show(5)

print("=== emp_projects JOIN projects (broadcast disabled -> forced shuffle/sort-merge join) ===")
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "-1")
project_assignments = emp_projects.join(projects, on="project_id", how="inner")
project_assignments.explain()
project_assignments.select("empno", "project_name", "budget").show(5)

spark.stop()
