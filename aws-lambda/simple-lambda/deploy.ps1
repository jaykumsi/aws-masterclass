# Deploys lambda_function.py to Floci AWS (LocalStack) as the "simple-lambda"
# function, using the AWS CLI.
#
# Prerequisites:
# - The docker stack in on-boarding/ must be running
#   (docker compose --env-file settings.config up -d), so Floci AWS is
#   reachable at http://localhost:4566.
# - The "floci" AWS CLI profile must exist (README.md Step 8 in the repo
#   root, or on-boarding/setup-floci-profile.ps1).

$Profile = "floci"
$FunctionName = "simple-lambda"
$RoleName = "simple-lambda-role"
$RoleArn = "arn:aws:iam::000000000000:role/$RoleName"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ZipPath = Join-Path $ScriptDir "function.zip"

# 1. Package the function
if (Test-Path $ZipPath) { Remove-Item $ZipPath -ErrorAction Stop }
Compress-Archive -Path (Join-Path $ScriptDir "lambda_function.py") -DestinationPath $ZipPath -ErrorAction Stop

# 2. Create the execution role if it doesn't already exist
# (the trust policy is read from a file, not passed inline, because Windows'
# argument-quoting mangles embedded double quotes when handed to the AWS CLI)
aws --profile $Profile iam get-role --role-name $RoleName 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    $TrustPolicyPath = Join-Path $ScriptDir "trust-policy.json"
    aws --profile $Profile iam create-role `
        --role-name $RoleName `
        --assume-role-policy-document "file://$TrustPolicyPath" | Out-Null
    Write-Output "Created IAM role $RoleName"
} else {
    Write-Output "IAM role $RoleName already exists"
}

# 3. Create the function, or update its code if it's already deployed
aws --profile $Profile lambda get-function --function-name $FunctionName 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
    aws --profile $Profile lambda update-function-code `
        --function-name $FunctionName `
        --zip-file "fileb://$ZipPath" | Out-Null
    Write-Output "Updated existing function: $FunctionName"
} else {
    aws --profile $Profile lambda create-function `
        --function-name $FunctionName `
        --runtime python3.12 `
        --handler lambda_function.handler `
        --role $RoleArn `
        --zip-file "fileb://$ZipPath" | Out-Null
    Write-Output "Created function: $FunctionName"
}

Write-Output "Done. Run the caller with: python lambda_caller.py"
