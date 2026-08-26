# AWS Lambda Operations

## Create a Simple Lambda

Files in [simple-lambda/](simple-lambda/):
* [lambda_function.py](simple-lambda/lambda_function.py) - the Lambda handler. Takes an event with an optional `name` field and returns a greeting, the received event, and a timestamp.
* [trust-policy.json](simple-lambda/trust-policy.json) - IAM trust policy for the Lambda execution role.
* [deploy.ps1](simple-lambda/deploy.ps1) - deploys the function using the AWS CLI.
* [lambda_caller.py](simple-lambda/lambda_caller.py) - invokes the deployed function using boto3 and prints the response.
* [lambda-details.md](simple-lambda/lambda-details.md) - what the function does, plus the full Step 1..N deploy walkthrough.

### Prerequisites
* The Docker stack in [on-boarding/](../on-boarding/) must be running, so Floci AWS (LocalStack) is reachable at `http://localhost:4566`:
  ```
  cd ..\on-boarding
  docker compose --env-file settings.config up -d
  ```
* The `floci` AWS CLI profile must exist (root [README.md](../README.md) Step 8):
  ```
  cd ..\on-boarding
  .\setup-floci-profile.ps1
  ```
* Install the Python dependency for the caller script:
  ```
  pip install -r simple-lambda\requirements.txt
  ```

### Deploy Lambda (using AWS CLI)
```
.\simple-lambda\deploy.ps1
```
This zips `lambda_function.py`, creates the `simple-lambda-role` IAM role if it doesn't already exist, and creates (or updates, if it already exists) the `simple-lambda` function - all via the `floci` AWS CLI profile.

### Run Lambda Caller
```
python simple-lambda\lambda_caller.py
```
This invokes `simple-lambda` with `{"name": "AWS Master Class"}` and prints the JSON response, e.g.:
```
{
  "statusCode": 200,
  "body": "{\"message\": \"Hello, AWS Master Class!\", \"receivedEvent\": {\"name\": \"AWS Master Class\"}, \"timestamp\": \"...\"}"
}
```

See [simple-lambda/lambda-details.md](simple-lambda/lambda-details.md) for the full step-by-step version, including verification and cleanup steps.

### Notes
* Everything above targets Floci AWS (LocalStack) via the `floci` AWS CLI profile, which points every service at `http://localhost:4566` with the throwaway `test`/`test` credentials - not a real AWS account.
* The trust policy is passed to the AWS CLI via `file://trust-policy.json` rather than inline JSON, because Windows' argument-quoting corrupts embedded double quotes when they're passed as a literal string.
