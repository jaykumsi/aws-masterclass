
## AWS Airflow Operations

### What is Airflow?
Apache Airflow (offered as a managed service on AWS called MWAA - Managed Workflows for
Apache Airflow) is a workflow **scheduler**. You describe a pipeline as Python code - a
**DAG** (Directed Acyclic Graph) of tasks and the order they must run in - and Airflow
runs it on schedule, retries failed tasks, and shows you a UI with every run's status.
Think of it as cron, but with dependencies between steps, retries, and visibility.

### How data flows
```mermaid
flowchart LR
    A[Schedule / Manual Trigger] --> B[Airflow Scheduler]
    B --> C[Task 1\nS3 Sensor]
    C --> D[Task 2\nEMR / Spark Submit]
    D --> E[Task 3\nLoad result to S3]
    E --> F[Task 4\nNotify / Branch]
    B -.->|status of every task| G[Airflow UI]
```

### Mind map
```mermaid
mindmap
  root((Airflow))
    DAG Basics
      Schedule Interval
      Task Dependencies
    Operators
      PythonOperator
      BashOperator
      S3 Sensor/Operator
      Lambda Invoke Operator
      EMR/Spark Submit Operator
    Connections and Variables
      AWS Connection
      Airflow Variables
    Orchestration Patterns
      S3 to EMR to S3
      Trigger from S3 event
      Branching
    Monitoring
      Airflow UI
      Retries and Alerts
```

### What we'll build
* DAG Basics
    * Write a simple DAG
    * Schedule Interval / Cron
    * Task Dependencies (>>, <<)
* Operators
    * PythonOperator
    * BashOperator
    * S3 Sensor / S3 Operators
    * Lambda Invoke Operator
    * EMR / Spark Submit Operator
* Connections & Variables
    * AWS Connection setup (pointing at the floci profile)
    * Airflow Variables and Connections via CLI
* Orchestration Patterns
    * ETL pipeline: S3 -> EMR/PySpark -> S3
    * Trigger a DAG from an S3 event
    * Branching (BranchPythonOperator)
* Monitoring
    * Airflow UI - DAG runs, task logs
    * Retries and alerting on failure
