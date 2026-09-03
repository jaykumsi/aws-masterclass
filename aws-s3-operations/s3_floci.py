"""Shared boto3 operations for the local Floci (LocalStack) S3 service."""

from __future__ import annotations

import os
from collections.abc import Iterator
from typing import Any

import boto3
from botocore.client import BaseClient
from botocore.exceptions import ClientError


DEFAULT_PROFILE = "floci"
DEFAULT_ENDPOINT = "http://localhost:4566"
DEFAULT_REGION = "us-east-1"


def s3_client(
    profile: str = DEFAULT_PROFILE,
    endpoint_url: str = DEFAULT_ENDPOINT,
    region: str = DEFAULT_REGION,
) -> BaseClient:
    """Create an S3 client using the local AWS profile and LocalStack endpoint."""
    session = boto3.Session(profile_name=profile, region_name=region)
    return session.client("s3", endpoint_url=endpoint_url)


def client_from_environment() -> BaseClient:
    """Create the client, allowing environment variables to override defaults."""
    return s3_client(
        profile=os.getenv("FLOCI_AWS_PROFILE", DEFAULT_PROFILE),
        endpoint_url=os.getenv("FLOCI_ENDPOINT_URL", DEFAULT_ENDPOINT),
        region=os.getenv("FLOCI_AWS_REGION", DEFAULT_REGION),
    )


def error_code(error: ClientError) -> str:
    return str(error.response.get("Error", {}).get("Code", "Unknown"))


def bucket_exists(client: BaseClient, bucket: str) -> bool:
    try:
        client.head_bucket(Bucket=bucket)
        return True
    except ClientError as error:
        if error_code(error) in {"404", "NoSuchBucket", "NotFound"}:
            return False
        raise


def object_exists(client: BaseClient, bucket: str, key: str) -> bool:
    try:
        client.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as error:
        if error_code(error) in {"404", "NoSuchKey", "NotFound"}:
            return False
        raise


def create_bucket(client: BaseClient, bucket: str, region: str = DEFAULT_REGION) -> None:
    if bucket_exists(client, bucket):
        raise ValueError(f"Bucket already exists: {bucket}")

    arguments: dict[str, Any] = {"Bucket": bucket}
    if region != "us-east-1":
        arguments["CreateBucketConfiguration"] = {"LocationConstraint": region}
    client.create_bucket(**arguments)


def list_buckets(client: BaseClient) -> list[dict[str, Any]]:
    return list(client.list_buckets().get("Buckets", []))


def iter_objects(
    client: BaseClient, bucket: str, prefix: str = ""
) -> Iterator[dict[str, Any]]:
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        yield from page.get("Contents", [])


def _delete_keys(client: BaseClient, bucket: str, objects: list[dict[str, str]]) -> None:
    for start in range(0, len(objects), 1000):
        batch = objects[start : start + 1000]
        client.delete_objects(Bucket=bucket, Delete={"Objects": batch, "Quiet": True})


def empty_bucket(client: BaseClient, bucket: str) -> None:
    """Delete current objects plus all versions/delete markers from a bucket."""
    version_entries: list[dict[str, str]] = []
    paginator = client.get_paginator("list_object_versions")
    for page in paginator.paginate(Bucket=bucket):
        for item in page.get("Versions", []):
            version_entries.append({"Key": item["Key"], "VersionId": item["VersionId"]})
        for item in page.get("DeleteMarkers", []):
            version_entries.append({"Key": item["Key"], "VersionId": item["VersionId"]})
    _delete_keys(client, bucket, version_entries)

    # Unversioned buckets do not return their objects from list_object_versions.
    current_entries = [{"Key": item["Key"]} for item in iter_objects(client, bucket)]
    _delete_keys(client, bucket, current_entries)


def delete_bucket(client: BaseClient, bucket: str, force: bool = False) -> None:
    if force:
        empty_bucket(client, bucket)
    client.delete_bucket(Bucket=bucket)


def rename_bucket(client: BaseClient, source: str, destination: str, region: str) -> int:
    """Copy all objects to a new bucket, then remove the original bucket."""
    if not bucket_exists(client, source):
        raise ValueError(f"Source bucket does not exist: {source}")
    if bucket_exists(client, destination):
        raise ValueError(f"Destination bucket already exists: {destination}")

    create_bucket(client, destination, region)
    copied_keys: list[dict[str, str]] = []
    try:
        for item in iter_objects(client, source):
            key = item["Key"]
            client.copy({"Bucket": source, "Key": key}, destination, key)
            copied_keys.append({"Key": key})
    except Exception:
        # Preserve both buckets if a copy fails; no source data is deleted.
        raise

    empty_bucket(client, source)
    client.delete_bucket(Bucket=source)
    return len(copied_keys)


def create_object(
    client: BaseClient,
    bucket: str,
    key: str,
    body: bytes,
    content_type: str | None = None,
) -> dict[str, Any]:
    if object_exists(client, bucket, key):
        raise ValueError(f"Object already exists: s3://{bucket}/{key}")
    arguments: dict[str, Any] = {"Bucket": bucket, "Key": key, "Body": body}
    if content_type:
        arguments["ContentType"] = content_type
    return client.put_object(**arguments)


def update_object(
    client: BaseClient,
    bucket: str,
    key: str,
    body: bytes,
    content_type: str | None = None,
) -> dict[str, Any]:
    if not object_exists(client, bucket, key):
        raise ValueError(f"Object does not exist: s3://{bucket}/{key}")
    arguments: dict[str, Any] = {"Bucket": bucket, "Key": key, "Body": body}
    if content_type:
        arguments["ContentType"] = content_type
    return client.put_object(**arguments)


def delete_object(client: BaseClient, bucket: str, key: str) -> None:
    if not object_exists(client, bucket, key):
        raise ValueError(f"Object does not exist: s3://{bucket}/{key}")
    client.delete_object(Bucket=bucket, Key=key)


def select_object(client: BaseClient, bucket: str, key: str) -> tuple[bytes, dict[str, Any]]:
    """Read an object's content and return it with selected response metadata."""
    response = client.get_object(Bucket=bucket, Key=key)
    metadata = {
        "ContentLength": response.get("ContentLength"),
        "ContentType": response.get("ContentType"),
        "ETag": response.get("ETag"),
        "LastModified": response.get("LastModified"),
    }
    return response["Body"].read(), metadata
