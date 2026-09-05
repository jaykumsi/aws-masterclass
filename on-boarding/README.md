# AWS local setup

This Docker Compose stack provides:

- LocalStack (called Floci in this course)
- Spark master and worker
- PySpark/JupyterLab
- Kafka
- FTP
- Netdata monitoring

The stack is defined by [docker-compose.yml](docker-compose.yml), with non-secret
defaults in [settings.config](settings.config). The Compose project name is
`tinitiate-aws-masterclass`, so its containers, network, and volumes are isolated
from other Compose projects.

## 1. Install and start Docker Desktop

On Windows 11, install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
and enable its WSL 2 backend. Wait until Docker Desktop reports that the engine is
running, then verify it from PowerShell:

```powershell
docker --version
docker compose version
```

If a command reports that `dockerDesktopLinuxEngine` cannot be found, Docker
Desktop is not running or has not finished starting.

## 2. Open the onboarding directory

From PowerShell:

```powershell
cd C:\Code\aws-masterclass\on-boarding
```

Change the `changeme_*` passwords in [settings.config](settings.config). Leave
the ports unchanged unless another program is already using one of them.

Never put a real LocalStack auth token in `settings.config` or commit one to GitHub.

## 3. Create a LocalStack account

Maintained LocalStack images require an account and auth token.

1. Open [LocalStack Web Application](https://app.localstack.cloud).
2. Sign in with GitHub, Google, Microsoft, SSO, or email.
3. For personal, non-commercial learning, select **Hobby plan**. It is the free
   option. Select **Trial plan** only when you intentionally want the Ultimate trial.
4. Finish account setup and copy the **Personal Auth Token** from Getting Started.

Treat the auth token like a password. Do not paste it into chat, screenshots,
source files, commits, or issue descriptions.

## 4. Set the LocalStack token safely

Set the token in the PowerShell window that will run Docker Compose. `Read-Host`
keeps the token out of PowerShell command history:

```powershell
$secureToken = Read-Host "Paste LocalStack token" -AsSecureString
$env:FLOCI_AUTH_TOKEN = [Net.NetworkCredential]::new("", $secureToken).Password
```

The environment variable lasts only for that PowerShell session. Set it again
after opening a new terminal or restarting the stack.

For macOS/Linux:

```bash
read -rsp "Paste LocalStack token: " FLOCI_AUTH_TOKEN
export FLOCI_AUTH_TOKEN
echo
```

## 5. Start the stack

From the `on-boarding` directory:

```powershell
docker compose --env-file settings.config pull
docker compose --env-file settings.config up -d
```

The first run downloads several large images and can take several minutes.

Check container status:

```powershell
docker compose --env-file settings.config ps
```

Inspect a service when it fails to start:

```powershell
docker compose --env-file settings.config logs --tail 100 floci-aws
docker compose --env-file settings.config logs --tail 100 kafka
```

## 6. Verify LocalStack

Check the LocalStack API health endpoint:

```powershell
curl.exe http://localhost:4566/_localstack/health
```

The response should list the LocalStack version, edition, and AWS service status.
The LocalStack logs must not contain `License activation failed`.

Opening `http://localhost:4566` directly may show a blank page. This is expected:
port `4566` is an AWS API gateway, not the graphical Resource Browser.

## 7. Connect the LocalStack Resource Browser

1. Open [LocalStack Web Application](https://app.localstack.cloud) and sign in.
2. Under **Instances**, click `localhost.localstack.cloud`.
3. If the instance is not detected, click **New Instance** and use
   `http://localhost:4566` as the endpoint.
4. In Chrome, allow **Local network access** for `app.localstack.cloud`, then
   refresh the page.
5. Open **Resource Browser**, choose **S3**, and select region `us-east-1`.

If the browser says it cannot connect to a licensed instance, check the running
version:

```powershell
docker compose --env-file settings.config exec floci-aws localstack --version
```

An old `3.8.x Community` container is unsupported by the current Resource Browser.
Confirm [docker-compose.yml](docker-compose.yml) uses
`localstack/localstack:latest`, set `FLOCI_AUTH_TOKEN`, then upgrade only LocalStack:

```powershell
docker compose --env-file settings.config pull floci-aws
docker compose --env-file settings.config up -d --force-recreate floci-aws
```

## 8. Create the `floci` AWS profile

The boto3 and AWS CLI examples use a profile named `floci` that points to port
`4566`. Run the appropriate setup script once.

Windows PowerShell:

```powershell
.\setup-floci-profile.ps1
```

macOS/Linux:

```bash
chmod +x ./setup-floci-profile.sh
./setup-floci-profile.sh
```

The scripts add only the `floci` profile and preserve other AWS profiles.

Test it:

```powershell
aws --profile floci s3api list-buckets
```

## 9. Run the boto3 S3 examples

Continue with the [S3 boto3 guide](../aws-s3-operations/aws-s3-readme.md), or run:

```powershell
cd ..\aws-s3-operations
python -m pip install -r requirements.txt
python scripts\01_create_bucket.py student-training-bucket
python scripts\04_list_buckets.py
```

Refresh **Resource Browser → S3** to see the new bucket.

## Service endpoints

| Service | Endpoint |
|---|---|
| LocalStack AWS API | `http://localhost:4566` |
| Spark master UI | `http://localhost:8080` |
| Spark worker UI | `http://localhost:8081` |
| JupyterLab | `http://localhost:8888` |
| PySpark application UI | `http://localhost:4040` |
| Kafka SASL/PLAIN broker | `localhost:9092` |
| Netdata dashboard | `http://localhost:19999` |
| FTP | `localhost:21` (`30000-30009` passive ports) |

## Stop or remove the stack

Stop containers while retaining data:

```powershell
docker compose --env-file settings.config stop
```

Start stopped containers after setting `FLOCI_AUTH_TOKEN`:

```powershell
docker compose --env-file settings.config start
```

Remove containers and keep named-volume data:

```powershell
docker compose --env-file settings.config down
```

Remove containers and permanently erase all LocalStack, Kafka, notebook, FTP,
and Netdata volume data:

```powershell
docker compose --env-file settings.config down -v
```

## Troubleshooting

- **Missing `FLOCI_AUTH_TOKEN`**: set it in the same terminal before running
  Compose. The Compose file intentionally stops early when the token is empty.
- **License activation failed**: confirm the token starts with `ls-`, has no
  surrounding quotes or spaces, and belongs to the active LocalStack workspace.
- **Resource Browser reports an old/unsupported image**: pull and recreate
  `floci-aws` using the commands in step 7.
- **Resource Browser reports a network failure**: allow Chrome local-network
  access and confirm the health endpoint responds.
- **`floci` profile not found**: run `setup-floci-profile.ps1` or
  `setup-floci-profile.sh` from this directory.
- **Port already allocated**: change the corresponding `*_PORT` value in
  `settings.config`, then recreate that service.
- **Container keeps restarting**: inspect it with
  `docker compose --env-file settings.config logs --tail 100 <service>`.
- **Kafka name conflict**: use this Compose file without adding hard-coded
  `container_name` values; Compose generates project-scoped names.

LocalStack references:

- [Authentication and auth tokens](https://docs.localstack.cloud/aws/getting-started/auth-token/)
- [Resource Browser](https://docs.localstack.cloud/aws/connecting/console/resource-browser/)
- [LocalStack plans](https://docs.localstack.cloud/aws/licensing/)
