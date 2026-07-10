"""
Evidence file storage service.

Backend is selected by STORAGE_BACKEND env: supabase | gcs | local.
When unset, falls back to the original behavior (GCS if USE_GCP and the
library is available, otherwise local disk under uploads/{motion_id}/).
Remote-backend errors raise EvidenceStorageError so the request fails
loudly — a silent local-disk fallback loses files on ephemeral hosting
while the DB row claims they exist. Local disk is only for backend=local.
"""
import os
import logging
from pathlib import Path

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class EvidenceStorageError(RuntimeError):
    """A storage backend failed to persist an evidence file."""


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


def _backend() -> str:
    explicit = os.getenv("STORAGE_BACKEND", "").lower()
    if explicit in ("supabase", "gcs", "local"):
        return explicit
    return "gcs" if (USE_GCP and _gcs_available) else "local"


def save_file(motion_id: str, filename: str, content: bytes) -> str:
    """
    Persist evidence file content and return the storage path.

    Raises ValueError for empty filenames.
    """
    clean_name = _sanitize_filename(filename)
    if not clean_name:
        raise ValueError("Filename must not be empty after sanitization")

    backend = _backend()
    if backend == "supabase":
        return _save_to_supabase(motion_id, clean_name, content)
    if backend == "gcs" and _gcs_available:
        return _save_to_gcs(motion_id, clean_name, content)
    return _save_to_disk(motion_id, clean_name, content)


def _save_to_disk(motion_id: str, filename: str, content: bytes) -> str:
    try:
        dest_dir = _UPLOADS_ROOT / motion_id
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / filename
        dest_path.write_bytes(content)
    except OSError as exc:
        raise EvidenceStorageError(f"Local disk write failed: {exc}") from exc
    return str(dest_path)


def _save_to_supabase(motion_id: str, filename: str, content: bytes) -> str:
    bucket = os.getenv("SUPABASE_EVIDENCE_BUCKET", "evidence")
    object_path = f"evidence/{motion_id}/{filename}"
    try:
        response = httpx.post(
            f"{os.environ['SUPABASE_URL']}/storage/v1/object/{bucket}/{object_path}",
            content=content,
            headers={
                "Authorization": f"Bearer {os.environ['SUPABASE_SERVICE_KEY']}",
                "Content-Type": "application/octet-stream",
                "x-upsert": "true",
            },
            timeout=30.0,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"Supabase storage returned {response.status_code}")
        return f"supabase://{bucket}/{object_path}"
    except Exception as exc:
        logger.error("Supabase upload failed for motion=%s: %s", motion_id, exc)
        raise EvidenceStorageError("Supabase upload failed") from exc


def _save_to_gcs(motion_id: str, filename: str, content: bytes) -> str:
    try:
        client = gcs_storage.Client()
        bucket = client.bucket(settings.GCS_BUCKET)
        blob_name = f"evidence/{motion_id}/{filename}"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(content)
        return f"gs://{settings.GCS_BUCKET}/{blob_name}"
    except Exception as exc:
        logger.error("GCS upload failed for motion=%s: %s", motion_id, exc)
        raise EvidenceStorageError("GCS upload failed") from exc
