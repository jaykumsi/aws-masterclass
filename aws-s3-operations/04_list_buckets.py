from cli_common import run
from s3_floci import client_from_environment, list_buckets


def main() -> None:
    buckets = list_buckets(client_from_environment())
    if not buckets:
        print("No buckets found")
        return
    for bucket in buckets:
        print(f"{bucket['Name']}\t{bucket.get('CreationDate', '')}")


if __name__ == "__main__":
    run(main)
