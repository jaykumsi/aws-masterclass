import argparse
import sys
from pathlib import Path

from cli_common import run
from s3_floci import client_from_environment, select_object


def main() -> None:
    parser = argparse.ArgumentParser(description="Read/download an object from Floci S3")
    parser.add_argument("bucket")
    parser.add_argument("key")
    parser.add_argument("--output", help="Write bytes to this file instead of stdout")
    args = parser.parse_args()
    body, metadata = select_object(client_from_environment(), args.bucket, args.key)

    if args.output:
        Path(args.output).write_bytes(body)
        print(f"Downloaded {len(body)} bytes to {args.output}")
        print(f"Metadata: {metadata}")
    else:
        sys.stdout.buffer.write(body)
        if body and not body.endswith(b"\n"):
            sys.stdout.buffer.write(b"\n")


if __name__ == "__main__":
    run(main)
