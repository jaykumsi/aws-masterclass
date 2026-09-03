import argparse

from cli_common import run
from s3_floci import client_from_environment, delete_bucket


def main() -> None:
    parser = argparse.ArgumentParser(description="Delete an S3 bucket from Floci AWS")
    parser.add_argument("bucket")
    parser.add_argument(
        "--force", action="store_true", help="Delete every object/version first"
    )
    args = parser.parse_args()
    delete_bucket(client_from_environment(), args.bucket, args.force)
    print(f"Deleted bucket: {args.bucket}")


if __name__ == "__main__":
    run(main)
