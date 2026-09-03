"""
CIVIX 2.0 — Plain Text Processor
Round 2A

Handles text/plain files. Detects encoding and decodes to UTF-8 string.
"""
import logging
import traceback

from .base import BaseProcessor, ProcessorResult

logger = logging.getLogger(__name__)


class TextProcessor(BaseProcessor):
    SUPPORTED_MIME_TYPES = ["text/plain", "text/csv", "text/markdown"]

    def process(self, file_bytes: bytes, mime_type: str, filename: str) -> ProcessorResult:
        try:
            # Try UTF-8 first, then fall back to latin-1 (never raises on arbitrary bytes)
            try:
                text = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                text = file_bytes.decode("latin-1")
                logger.warning(f"Text file {filename} decoded as latin-1 (not UTF-8).")

            char_count = len(text.strip())

            media_metadata = {
                "extraction_method": "direct_text_decode",
                "char_count": char_count,
                "encoding_detected": "utf-8" if file_bytes.decode("utf-8", errors="replace") == text else "latin-1",
            }

            return ProcessorResult(
                extracted_text=text,
                media_metadata=media_metadata,
                extraction_notes=f"Plain text decoded: {char_count} chars.",
                success=True,
            )

        except Exception as e:
            logger.error(f"Text processing failed for {filename}: {e}")
            return ProcessorResult(
                success=False,
                error=f"Text processing error: {str(e)}\n{traceback.format_exc()}"
            )
