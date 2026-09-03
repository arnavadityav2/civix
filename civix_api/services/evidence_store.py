"""
CIVIX 2.0 — Evidence Local File Store
Round 2A

Manages storing uploaded evidence files on the local filesystem with
a content-addressed directory structure keyed on SHA-256 hash.

Directory layout:
  {EVIDENCE_STORE_ROOT}/{hash_prefix_4}/{full_sha256_hex}/{sanitized_filename}

This structure is:
  - Collision-proof: path is keyed on hash, not filename.
  - Deduplication-aware: same hash → same path, no copy needed.
  - S3-portable: path can be used verbatim as an S3 object key prefix.
"""
import hashlib
import os
import shutil
import logging
from pathlib import Path
from typing import Tuple

logger = logging.getLogger(__name__)

# Default store root — resolved relative to the project root.
# Override via env var CIVIX_EVIDENCE_STORE_PATH.
_DEFAULT_STORE_ROOT = Path(r"c:\data\civix_demo\evidence_store")


def get_store_root() -> Path:
    raw = os.environ.get("CIVIX_EVIDENCE_STORE_PATH", r"c:\data\civix_demo\evidence_store")
    root = Path(raw) if raw else _DEFAULT_STORE_ROOT
    root.mkdir(parents=True, exist_ok=True)
    return root


def _build_storage_path(sha256_hex: str, filename: str) -> Path:
    """Returns the canonical on-disk path for an artifact."""
    prefix = sha256_hex[:4]
    store_root = get_store_root()
    return store_root / prefix / sha256_hex / filename


def compute_sha256(data: bytes) -> Tuple[bytes, str]:
    """Returns (raw_bytes, hex_string)."""
    digest = hashlib.sha256(data).digest()
    return digest, digest.hex()


def sanitize_filename(filename: str) -> str:
    """Strip directory components and replace unsafe characters."""
    name = Path(filename).name          # strips any path traversal
    # Replace whitespace and common unsafe chars with underscores
    safe = "".join(c if (c.isalnum() or c in "._-") else "_" for c in name)
    return safe or "evidence_file"


def store_file(file_bytes: bytes, original_filename: str) -> Tuple[str, str, bool]:
    """
    Saves file_bytes to the content-addressed store.

    Returns:
        storage_uri   — local:// URI string
        sha256_hex    — hex representation of SHA-256 digest
        is_duplicate  — True if the file already existed at the target path
    """
    sha256_raw, sha256_hex = compute_sha256(file_bytes)
    safe_name = sanitize_filename(original_filename)
    dest_path = _build_storage_path(sha256_hex, safe_name)

    is_duplicate = dest_path.exists()

    if not is_duplicate:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(file_bytes)
        logger.info(f"Stored evidence file: {dest_path} ({len(file_bytes)} bytes)")
    else:
        logger.info(f"Duplicate evidence file detected at: {dest_path}")

    storage_uri = f"local://civix_evidence_store/{dest_path.relative_to(get_store_root()).as_posix()}"
    return storage_uri, sha256_hex, is_duplicate


def retrieve_file(storage_uri: str) -> bytes:
    """
    Reads a stored file by its storage_uri.

    Raises FileNotFoundError if the path does not exist.
    """
    if not storage_uri.startswith("local://civix_evidence_store/"):
        raise ValueError(f"Unsupported storage_uri scheme: {storage_uri}")

    relative = storage_uri.removeprefix("local://civix_evidence_store/")
    full_path = get_store_root() / relative

    if not full_path.exists():
        raise FileNotFoundError(f"Evidence file not found at: {full_path}")

    return full_path.read_bytes()


def verify_integrity(storage_uri: str, expected_sha256_hex: str) -> bool:
    """
    Re-computes SHA-256 of the stored file and compares to the expected hash.
    Returns True if hashes match.
    """
    try:
        data = retrieve_file(storage_uri)
        _, actual_hex = compute_sha256(data)
        return actual_hex == expected_sha256_hex
    except FileNotFoundError:
        return False
