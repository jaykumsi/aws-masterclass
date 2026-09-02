"""
Prep step (no Spark yet): the datasets in landing_zone/{csv,json,parquet}/*.zip
are raw zip archives with messy internal folder nesting. Spark can't read
zip archives directly, so this unzips each one in memory and re-uploads the
individual csv/json/parquet files to flat, predictable prefixes:

    extracted/<dataset>/<format>/<table>/part_NNNNNNN.<ext>

e.g. extracted/04_many_small_csv_emp/csv/emp/part_0000001.csv

Note: extracted files are written to a *different* bucket than the source
zips -- landing-zone (hyphen), not landing_zone (underscore). Spark's S3A
connector builds a Java URI out of the bucket name (s3a://bucket/...), and
Java's URI parser rejects underscores in the host component (silently
returns a null host -> "bucket is null/empty" errors deep in hadoop-aws).
Real AWS S3 disallows underscores in bucket names for this exact reason;
floci is more lenient and let landing_zone get created anyway. Rather than
touch the existing landing_zone bucket, we just land Spark-readable copies
in a second, correctly-named bucket.

Run this once (on the host, same as floci_s3_get_data.py) before the
numbered lesson scripts. Dataset 10 (the "ultra" one-million-files zip) is
deliberately excluded here -- it's slow to extract on purpose, and gets its
own step in the many-small-files lesson.
"""
import io
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from botocore.exceptions import ClientError
from floci_s3_bucket_operations import s3_client

SOURCE_BUCKET = "landing_zone"
DEST_BUCKET = "landing-zone"
FORMAT_DIRS = ("csv", "json", "parquet")


def ensure_dest_bucket():
    try:
        s3_client.head_bucket(Bucket=DEST_BUCKET)
    except ClientError:
        s3_client.create_bucket(Bucket=DEST_BUCKET)
        print(f"Created bucket: {DEST_BUCKET}")

ZIP_KEYS = [
    "csv/04_many_small_csv_emp.zip",
    "csv/05_many_small_csv_multiple_tables.zip",
    "csv/06_many_large_csv_emp.zip",
    "parquet/07_many_small_parquet_transaction.zip",
    "parquet/08_many_small_parquet_multiple_tables.zip",
    "parquet/09_many_large_parquet_sales.zip",
    "11_millions_updates_deletes.zip",
]


def extract_zip(zip_key):
    zip_stem = Path(zip_key).stem
    body = s3_client.get_object(Bucket=SOURCE_BUCKET, Key=zip_key)["Body"].read()
    archive = zipfile.ZipFile(io.BytesIO(body))

    count = 0
    for name in archive.namelist():
        if name.endswith("/"):
            continue
        parts = name.split("/")
        fmt = next((p for p in parts if p in FORMAT_DIRS), None)
        if fmt is None:
            continue  # e.g. _manifests/*.json -- not a data file, skip
        table = parts[parts.index(fmt) + 1]
        filename = parts[-1]
        dest_key = f"extracted/{zip_stem}/{fmt}/{table}/{filename}"
        s3_client.put_object(Bucket=DEST_BUCKET, Key=dest_key, Body=archive.read(name))
        count += 1

    print(f"{zip_key}: extracted {count} files -> {DEST_BUCKET}/extracted/{zip_stem}/")


def main():
    ensure_dest_bucket()
    for zip_key in ZIP_KEYS:
        extract_zip(zip_key)


if __name__ == "__main__":
    main()
