# Creates (or updates) a "floci" AWS CLI profile pointing at the local
# Floci AWS (LocalStack) stack, so any AWS CLI command or boto3 script in
# this repo can use --profile floci / profile_name="floci" instead of
# hardcoding credentials or an --endpoint-url every time.
#
# Safe to run even if %USERPROFILE%\.aws already has other profiles in it -
# this only adds a "floci" section; it never touches or removes anything
# else in those files.

function Add-ProfileSection {
    param(
        [string]$Path,
        [string]$Marker,
        [string]$Content
    )

    if ((Test-Path $Path) -and (Select-String -Path $Path -Pattern $Marker -Quiet)) {
        Write-Output "$Marker already present in $Path - left unchanged"
        return
    }

    Add-Content -Path $Path -Value $Content
    Write-Output "Added $Marker to $Path"
}

$AwsDir = Join-Path $env:USERPROFILE ".aws"
$CredentialsPath = Join-Path $AwsDir "credentials"
$ConfigPath = Join-Path $AwsDir "config"

New-Item -ItemType Directory -Force -Path $AwsDir | Out-Null
if (-not (Test-Path $CredentialsPath)) { New-Item -ItemType File -Path $CredentialsPath | Out-Null }
if (-not (Test-Path $ConfigPath)) { New-Item -ItemType File -Path $ConfigPath | Out-Null }

Add-ProfileSection -Path $CredentialsPath -Marker '^\[floci\]$' -Content @"

[floci]
aws_access_key_id = test
aws_secret_access_key = test
"@

Add-ProfileSection -Path $ConfigPath -Marker '^\[profile floci\]$' -Content @"

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
  endpoint_url = http://localhost:4566
"@

Write-Output "Test it with: aws --profile floci lambda list-functions"
