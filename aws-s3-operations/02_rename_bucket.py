import argparse

from cli_common import run
from s3_floci import DEFAULT_REGION, client_from_environment, rename_bucket


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rename a Floci S3 bucket by copying its objects"
    )
    parser.add_argument("source")
    parser.add_argument("destination")
    parser.add_argument("--region", default=DEFAULT_REGION)
    args = parser.parse_args()
    count = rename_bucket(
        client_from_environment(), args.source, args.destination, args.region
    )
    print(f"Renamed {args.source} to {args.destination}; copied {count} object(s)")


if __name__ == "__main__":
    run(main)
