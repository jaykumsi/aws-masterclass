import argparse

from cli_common import read_input, run
from s3_floci import client_from_environment, update_object


def main() -> None:
    parser = argparse.ArgumentParser(description="Update an existing object in Floci S3")
    parser.add_argument("bucket")
    parser.add_argument("key")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--file")
    source.add_argument("--text")
    parser.add_argument("--content-type")
    args = parser.parse_args()
    body, detected_type = read_input(args.file, args.text)
    response = update_object(
        client_from_environment(),
        args.bucket,
        args.key,
        body,
        args.content_type or detected_type,
    )
    print(f"Updated s3://{args.bucket}/{args.key} ETag={response.get('ETag')}")


if __name__ == "__main__":
    run(main)
