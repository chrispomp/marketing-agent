import io
import os
import time
from typing import Tuple
from google.cloud import storage

_BUCKET = None
_BUCKET_NAME = None

def _bucket():
    global _BUCKET, _BUCKET_NAME
    if _BUCKET is None:
        bucket_uri = os.environ["GCS_BUCKET"]
        if not bucket_uri.startswith("gs://"):
            raise ValueError("GCS_BUCKET must start with gs://")
        _BUCKET_NAME = bucket_uri.replace("gs://", "", 1)
        client = storage.Client()
        _BUCKET = client.bucket(_BUCKET_NAME)
    return _BUCKET, _BUCKET_NAME

def upload_bytes(content: bytes, path: str, content_type: str) -> str:
    bucket, bucket_name = _bucket()
    blob = bucket.blob(path)
    blob.upload_from_file(io.BytesIO(content), content_type=content_type)
    blob.cache_control = "public, max-age=3600"
    blob.patch()
    return f"gs://{bucket_name}/{path}"

def upload_file(local_path: str, dest_path: str, content_type: str) -> str:
    bucket, bucket_name = _bucket()
    blob = bucket.blob(dest_path)
    blob.content_type = content_type
    blob.upload_from_filename(local_path)
    return f"gs://{bucket_name}/{dest_path}"

def gcs_path(prefix: str, name: str, ext: str) -> str:
    ts = int(time.time() * 1000)
    return f"{prefix}/{ts}_{name}.{ext}"
