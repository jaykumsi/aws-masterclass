import argparse

from cli_common import run
from s3_floci import client_from_environment, delete_object


def main() -> None:
    parser = argparse.ArgumentParser(description="Delete an object from Floci S3")
    parser.add_argument("bucket")
    parser.add_argument("key")
    args = parser.parse_args()
    delete_object(client_from_environment(), args.bucket, args.key)
    print(f"Deleted s3://{args.bucket}/{args.key}")


if __name__ == "__main__":
    run(main)
