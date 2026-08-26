#!/usr/bin/env bash
# Creates (or updates) a "floci" AWS CLI profile pointing at the local
# Floci AWS (LocalStack) stack, so any AWS CLI command or boto3 script in
# this repo can use --profile floci / profile_name="floci" instead of
# hardcoding credentials or an --endpoint-url every time.
#
# Safe to run even if ~/.aws already has other profiles in it - this only
# adds a "floci" section; it never touches or removes anything else in
# those files.

set -euo pipefail

add_profile_section() {
    local path="$1"
    local marker="$2"
    local content="$3"

    if [ -f "$path" ] && grep -q "^${marker}$" "$path"; then
        echo "${marker} already present in ${path} - left unchanged"
        return
    fi

    printf '%s\n' "$content" >> "$path"
    echo "Added ${marker} to ${path}"
}

AWS_DIR="$HOME/.aws"
CREDENTIALS_PATH="$AWS_DIR/credentials"
CONFIG_PATH="$AWS_DIR/config"

mkdir -p "$AWS_DIR"
touch "$CREDENTIALS_PATH" "$CONFIG_PATH"

add_profile_section "$CREDENTIALS_PATH" '\[floci\]' '
[floci]
aws_access_key_id = test
aws_secret_access_key = test'

add_profile_section "$CONFIG_PATH" '\[profile floci\]' '
[profile floci]
region = us-east-1
output = json
services = floci-services

[services floci-services]
s3 =
  endpoint_url = http://localhost:4566
lambda =
  endpoint_url = http://localhost:4566
iam =
  endpoint_url = http://localhost:4566
dynamodb =
  endpoint_url = http://localhost:4566
sqs =
  endpoint_url = http://localhost:4566
sns =
  endpoint_url = http://localhost:4566
cloudwatch =
  endpoint_url = http://localhost:4566
logs =
  endpoint_url = http://localhost:4566'

echo "Test it with: aws --profile floci lambda list-functions"
