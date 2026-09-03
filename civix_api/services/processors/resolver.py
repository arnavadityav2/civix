"""
CIVIX 2.0 — Processor Resolver
Round 2A

Resolves which processor to use for a given MIME type.
Returns an UnsupportedProcessor result for unknown/unprocessable types.
"""
import logging
import mimetypes

from .base import BaseProcessor, ProcessorResult
from .pdf_processor import PDFProcessor
from .text_processor import TextProcessor
from .image_processor import ImageProcessor

logger = logging.getLogger(__name__)

# Maximum supported file size (bytes). Enforced before calling processor.
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB

# Supported MIME types for Round 2A
SUPPORTED_MIME_TYPES = {
    # PDF
    "application/pdf": PDFProcessor,
    # Plain text variants
    "text/plain": TextProcessor,
    "text/csv": TextProcessor,
    "text/markdown": TextProcessor,
    # Images
    "image/png": ImageProcessor,
    "image/jpeg": ImageProcessor,
    "image/jpg": ImageProcessor,
    "image/tiff": ImageProcessor,
    "image/bmp": ImageProcessor,
    "image/webp": ImageProcessor,
    # Video (Round 2B)
    # "video/mp4": VideoProcessor,
}


def detect_mime_type(file_bytes: bytes, filename: str) -> str:
    """
    Detect MIME type from file content (first bytes) using mimetypes.
    Falls back to filename-based guess if content detection fails.
    """
    # Try to detect from magic bytes
    # PyMuPDF can detect PDFs; for other types use mimetypes + filename
    if file_bytes[:4] == b"%PDF":
        return "application/pdf"

    if file_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"

    if file_bytes[:2] in (b"\xff\xd8",):
        return "image/jpeg"

    if file_bytes[:4] in (b"RIFF", b"RIFX") and file_bytes[8:12] == b"WEBP":
        return "image/webp"

    if file_bytes[:2] in (b"II", b"MM") and file_bytes[2:4] in (b"\x2a\x00", b"\x00\x2a"):
        return "image/tiff"

    # Heuristic: try to decode as UTF-8 text
    if len(file_bytes) > 0:
        try:
            file_bytes[:512].decode("utf-8")
            # Check if it looks like text (high proportion of printable chars)
            printable = sum(1 for b in file_bytes[:512] if 0x09 <= b <= 0x7e or b >= 0x80)
            if printable / min(512, len(file_bytes)) > 0.85:
                mime, _ = mimetypes.guess_type(filename)
                if mime and mime.startswith("text/"):
                    return mime
                return "text/plain"
        except UnicodeDecodeError:
            pass

    # Final fallback: filename-based guess
    mime, _ = mimetypes.guess_type(filename)
    return mime or "application/octet-stream"


class ProcessorResolver:
    """
    Selects the correct processor for a file and runs it.
    Never raises — returns ProcessorResult with success=False on any error.
    """

    @staticmethod
    def resolve(file_bytes: bytes, original_filename: str) -> tuple[str, ProcessorResult]:
        """
        Returns (detected_mime_type, ProcessorResult).
        """
        # Size check
        if len(file_bytes) == 0:
            return "application/octet-stream", ProcessorResult(
                success=False, error="Empty file — cannot process."
            )

        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            size_mb = len(file_bytes) / (1024 * 1024)
            return "application/octet-stream", ProcessorResult(
                success=False,
                error=f"File size {size_mb:.1f}MB exceeds maximum of {MAX_FILE_SIZE_BYTES // (1024*1024)}MB."
            )

        # Detect MIME type from content (not from client-provided Content-Type)
        mime_type = detect_mime_type(file_bytes, original_filename)
        logger.info(f"Detected MIME type: {mime_type} for file: {original_filename}")

        processor_class = SUPPORTED_MIME_TYPES.get(mime_type)

        if processor_class is None:
            return mime_type, ProcessorResult(
                success=False,
                error=f"Unsupported file type: {mime_type}. "
                      f"Supported types: {sorted(SUPPORTED_MIME_TYPES.keys())}",
                media_metadata={"detected_mime": mime_type},
            )

        processor = processor_class()
        result = processor.process(file_bytes, mime_type, original_filename)
        return mime_type, result
