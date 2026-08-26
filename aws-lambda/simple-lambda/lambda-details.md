# Simple Lambda

## What it does

[lambda_function.py](lambda_function.py) is a minimal Lambda handler. It takes an event with an
optional `name` field and returns:
* `statusCode: 200`
* a JSON body containing a greeting (`"Hello, <name>!"`), the event it received back (`receivedEvent`), and a UTC timestamp.

If the event has no `name` field, it defaults to `"World"`. There are no external dependencies and
no AWS service calls inside the function - it's the simplest possible Lambda, used to prove the
deploy → invoke pipeline works end to end.

## Deploy to Floci - step by step

**Step 1 - Start Floci AWS**
* From [on-boarding/](../../on-boarding/):
  ```
  docker compose --env-file settings.config up -d
  ```
* Confirm it's healthy:
  ```
  docker compose --env-file settings.config ps floci-aws
  ```

**Step 2 - Create the `floci` AWS CLI profile** (one-time, skip if already done)
* From [on-boarding/](../../on-boarding/):
  ```
  .\setup-floci-profile.ps1
  ```
* See root [README.md](../../README.md) Step 8 for details.

**Step 3 - Install the caller's Python dependency**
* From this folder:
  ```
  pip install -r requirements.txt
  ```

**Step 4 - Deploy the function**
* From this folder:
  ```
  .\deploy.ps1
  ```
* This zips [lambda_function.py](lambda_function.py), creates the `simple-lambda-role` IAM role from [trust-policy.json](trust-policy.json) if it doesn't already exist, and creates (or updates, if already deployed) the `simple-lambda` function.

**Step 5 - Verify the deployment**
```
aws --profile floci lambda get-function --function-name simple-lambda
```
* Look for `"State": "Active"` in the output.

**Step 6 - Invoke it**
```
python lambda_caller.py
```
* Expected output:
  ```
  {
    "statusCode": 200,
    "body": "{\"message\": \"Hello, AWS Master Class!\", \"receivedEvent\": {\"name\": \"AWS Master Class\"}, \"timestamp\": \"...\"}"
  }
  ```

**Step 7 - Clean up** (optional)
```
aws --profile floci lambda delete-function --function-name simple-lambda
aws --profile floci iam delete-role --role-name simple-lambda-role
```
