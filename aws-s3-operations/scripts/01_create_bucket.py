import argparse

from cli_common import run
from s3_floci import DEFAULT_REGION, client_from_environment, create_bucket


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an S3 bucket in Floci AWS")
    parser.add_argument("bucket")
    parser.add_argument("--region", default=DEFAULT_REGION)
    args = parser.parse_args()
    create_bucket(client_from_environment(), args.bucket, args.region)
    print(f"Created bucket: {args.bucket}")


if __name__ == "__main__":
    run(main)
