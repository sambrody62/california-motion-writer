"""
Evidence file storage service.

In development (USE_GCP=false), files are stored under uploads/{motion_id}/.
In production with GCP available, files are uploaded to GCS with a local fallback.
"""
import os
import logging
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)

USE_GCP = os.getenv("USE_GCP", "true").lower() == "true"

if USE_GCP:
    try:
        from google.cloud import storage as gcs_storage
        _gcs_available = True
    except ImportError:
        _gcs_available = False
        logger.warning("google-cloud-storage not available; falling back to local disk")
else:
    _gcs_available = False

_UPLOADS_ROOT = Path("uploads")


def _sanitize_filename(filename: str) -> str:
    """Return the basename only, stripping any path components."""
    return os.path.basename(filename)


def save_file(motion_id: str, filename: str, content: bytes) -> str:
    """
    Persist evidence file content and return the storage path.

    Raises ValueError for empty filenames.
    Delegates to GCS when available, otherwise writes to local disk.
    """
    clean_name = _sanitize_filename(filename)
    if not clean_name:
        raise ValueError("Filename must not be empty after sanitization")

    if USE_GCP and _gcs_available:
        return _save_to_gcs(motion_id, clean_name, content)
    return _save_to_disk(motion_id, clean_name, content)


def _save_to_disk(motion_id: str, filename: str, content: bytes) -> str:
    dest_dir = _UPLOADS_ROOT / motion_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / filename
    dest_path.write_bytes(content)
    return str(dest_path)


def _save_to_gcs(motion_id: str, filename: str, content: bytes) -> str:
    try:
        client = gcs_storage.Client()
        bucket = client.bucket(settings.GCS_BUCKET)
        blob_name = f"evidence/{motion_id}/{filename}"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(content)
        return f"gs://{settings.GCS_BUCKET}/{blob_name}"
    except Exception as exc:
        logger.error("GCS upload failed for evidence id=%s; falling back to disk: %s", motion_id, exc)
        return _save_to_disk(motion_id, filename, content)
