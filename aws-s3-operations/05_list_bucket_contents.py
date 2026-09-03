import argparse

from cli_common import run
from s3_floci import client_from_environment, iter_objects


def main() -> None:
    parser = argparse.ArgumentParser(
        description="List all virtual folders and files in a Floci S3 bucket"
    )
    parser.add_argument("bucket")
    parser.add_argument("--prefix", default="")
    args = parser.parse_args()

    objects = list(iter_objects(client_from_environment(), args.bucket, args.prefix))
    if not objects:
        print("No objects found")
        return

    # S3 has no real folders, so infer every virtual folder from key paths.
    folders: set[str] = set()
    for item in objects:
        parts = item["Key"].split("/")
        for index in range(1, len(parts)):
            folders.add("/".join(parts[:index]) + "/")
    for folder in sorted(folders):
        print(f"FOLDER\t0\t{folder}")
    for item in objects:
        if not item["Key"].endswith("/"):
            print(f"FILE\t{item.get('Size', 0)}\t{item['Key']}")


if __name__ == "__main__":
    run(main)
