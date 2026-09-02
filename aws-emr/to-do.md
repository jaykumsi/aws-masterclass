# There is data here
* C:\code\aws-floci\data\s3\landing_zone
* Create simple Joins, group by creating target files
* I want to see spark UI run details and understand shuffl and other issues 
* I want to clearly understand code as DAGs  apps > dag > jobs > stage > task
# Spark Application = ETL Script
* **DAG** = The step-by-step plan for your data. Spark makes a DAG when you call an action. It shows how to change and move your data.
  * **Job** (The Goal): Created every time your script hits an "action" (like .write() or .count()). A DAG can contain multiple jobs.
  * **Stage** (The Boundaries): Jobs are split into stages based on data movement. A new stage starts whenever data needs to be shuffled across the network (like a .groupBy() or .join()).
  * **Task** (The Work): The smallest unit of execution. Stages are split into tasks. Each task does the exact same work but on a different small piece (partition) of your data.

* Create simple and easy to understand code and add more data as neeed tp demonstrate one at a file per code file