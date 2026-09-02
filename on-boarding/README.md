## [AWS Local Setup ](on-boarding/README.md)
* AWS Floci Docker
* PySpark
* Graphana (Cloud Watch Alternative)
* Setup and .aws folder instructions for floci
* Kafka

### Docker stack

[on-boarding/docker-compose.yml](on-boarding/docker-compose.yml) + [on-boarding/settings.config](on-boarding/settings.config)
bring up Floci (LocalStack) AWS, a PySpark cluster with UI, Kafka, an FTP server, and Netdata monitoring in one shot.
The Docker Compose project is named `tinitiate-aws-masterclass` (set via the `name:` field in docker-compose.yml), so
all containers, the network, and the named volumes it creates are prefixed `tinitiate-aws-masterclass_*` regardless
of which folder you run it from.

#### Install guide

**Step 1 - Install Docker Desktop**
* Windows 11 needs [Docker Desktop](https://www.docker.com/products/docker-desktop/) with the WSL2 backend enabled (Docker Desktop prompts you to enable WSL2 on first run if it isn't already).
* Start Docker Desktop and wait for it to show "Engine running" before continuing.
* Verify from PowerShell:
  ```
  docker --version
  docker compose version
  ```

**Step 2 - Get the project files**
* Change into the `on-boarding` folder, which contains [docker-compose.yml](on-boarding/docker-compose.yml) and [settings.config](on-boarding/settings.config):
  ```
  cd on-boarding
  ```

**Step 3 - Set your passwords**
* Open [settings.config](on-boarding/settings.config) and replace every `changeme_*` value with your own password/secret.
* Leave the port numbers as-is unless something else on your machine already uses them.

**Step 4 - Start the stack**
* From the `on-boarding` folder, run in an admin command terminal:
  ```
  docker compose --env-file settings.config up -d
  ```
* `-d` runs it in the background. The first run will take a few minutes while Docker pulls the images.

**Step 5 - Check everything is healthy**
* List running containers and their status:
  ```
  docker compose --env-file settings.config ps
  ```
* Tail logs for a specific service if something isn't starting (e.g. `kafka`, `floci-aws`, `pyspark`):
  ```
  docker compose --env-file settings.config logs -f kafka
  ```

**Step 6 - Open the UIs**
* Endpoints (default ports, all overridable in [settings.config](on-boarding/settings.config)):
  * Floci AWS (LocalStack) edge: `http://localhost:4566`
  * Spark master UI: `http://localhost:8080`
  * Spark worker UI: `http://localhost:8081`
  * PySpark Jupyter: `http://localhost:8888` (token in `PYSPARK_JUPYTER_TOKEN`)
  * PySpark application UI: `http://localhost:4040`
  * Kafka broker (SASL/PLAIN): `localhost:9092`
  * Netdata dashboard: `http://localhost:19999`
  * FTP server: `localhost:21` (passive range `30000-30009`)
* Netdata runs on host networking with the Docker socket mounted, so it automatically monitors every other container in the stack - no extra wiring needed.

**Step 7 - Stop / restart the stack**
* Stop but keep all data (buckets, notebooks, Kafka topics, FTP files):
  ```
  docker compose --env-file settings.config stop
  ```
* Start it again later:
  ```
  docker compose --env-file settings.config start
  ```
* Fully tear down (also removes containers, keeps named volumes/data):
  ```
  docker compose --env-file settings.config down
  ```
* Fully tear down **and** wipe all stored data:
  ```
  docker compose --env-file settings.config down -v
  ```

**Step 8 - Create the `.aws` profile for Floci**
* AWS CLI/boto3 tools normally read credentials from a `credentials` and `config` file under your `.aws` folder. Run the setup script once to add a `floci` profile there, pointing every service at `http://localhost:4566`:
  * **Windows** (`%USERPROFILE%\.aws\credentials` / `config`), from PowerShell:
    ```
    .\setup-floci-profile.ps1
    ```
  * **Mac** (`~/.aws/credentials` / `config`), from Terminal:
    ```
    chmod +x ./setup-floci-profile.sh
    ./setup-floci-profile.sh
    ```
* It's safe to run even if you already have other AWS profiles - it only adds a `[floci]` / `[profile floci]` section and never touches anything else in those files. Running it again is a no-op if the profile already exists.
* Verify it works:
  ```
  aws --profile floci lambda list-functions
  ```
* Every script under [aws-lambda/](aws-lambda/) uses this profile (`--profile floci` for the AWS CLI, `boto3.Session(profile_name="floci")` for Python) instead of hardcoding credentials or an endpoint URL.

**Troubleshooting**
* "port is already allocated" - another app on your machine is using that port; change the matching `*_PORT` value in [settings.config](on-boarding/settings.config) and rerun `up -d`.
* A container keeps restarting - run `docker compose --env-file settings.config logs -f <service-name>` to see why.
* Forgot the `--env-file` flag - Compose falls back to `.env` (which doesn't exist here), so every `${VAR}` resolves empty and containers fail to start; always include `--env-file settings.config`.
* `floci-aws` exits with "License activation failed" - only happens if you switch the image back to `localstack/localstack:latest`; newer LocalStack releases require a free-account auth token even for community services. The compose file pins `localstack/localstack:3.8`, which doesn't need one.
* Images pull errors for `bitnami/kafka` or `bitnami/spark` - Broadcom removed the free `latest` tags for most Bitnami images in 2025. This stack already avoids them (Kafka runs on `confluentinc/cp-kafka`, Spark on the official `apache/spark` image).