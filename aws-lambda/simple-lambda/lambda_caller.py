import json

import boto3

PROFILE = "floci"
FUNCTION_NAME = "simple-lambda"


def main():
    session = boto3.Session(profile_name=PROFILE)
    client = session.client("lambda")

    payload = {"name": "AWS Master Class"}
    response = client.invoke(
        FunctionName=FUNCTION_NAME,
        InvocationType="RequestResponse",
        Payload=json.dumps(payload).encode("utf-8"),
    )

    result = json.loads(response["Payload"].read())
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
