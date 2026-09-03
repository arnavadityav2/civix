"""
CIVIX 2.0 — Image Processor (Pillow)
Round 2A

Extracts image metadata (dimensions, format, mode, EXIF) using Pillow.
OCR (Tesseract) is deferred to Round 2B — Tesseract is not yet installed.

When OCR becomes available, pytesseract.image_to_string() will be called
here and the result placed in extracted_text.
"""
import io
import logging
import traceback

from .base import BaseProcessor, ProcessorResult

logger = logging.getLogger(__name__)


class ImageProcessor(BaseProcessor):
    SUPPORTED_MIME_TYPES = [
        "image/png", "image/jpeg", "image/jpg", "image/tiff",
        "image/bmp", "image/webp", "image/gif",
    ]

    def process(self, file_bytes: bytes, mime_type: str, filename: str) -> ProcessorResult:
        try:
            from PIL import Image, ExifTags
        except ImportError:
            return ProcessorResult(
                success=False,
                error="Pillow is not installed. Cannot process image."
            )

        try:
            img = Image.open(io.BytesIO(file_bytes))
            width, height = img.size
            img_format = img.format
            img_mode = img.mode

            # Extract EXIF metadata safely
            exif_data = {}
            try:
                raw_exif = img._getexif()
                if raw_exif:
                    for tag_id, value in raw_exif.items():
                        tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                        # Only include simple scalar EXIF values to keep JSONB clean
                        if isinstance(value, (str, int, float, bool)):
                            exif_data[tag_name] = value
            except Exception:
                pass  # EXIF extraction is best-effort

            media_metadata = {
                "width": width,
                "height": height,
                "format": img_format,
                "mode": img_mode,
                "exif": exif_data,
                "extraction_method": "pillow_metadata_only",
                "ocr_available": False,
                "ocr_deferred": "Round 2B — Tesseract not yet installed",
            }

            notes = (
                f"Image metadata extracted: {width}x{height} {img_format}/{img_mode}. "
                "OCR deferred to Round 2B (Tesseract not installed)."
            )

            return ProcessorResult(
                extracted_text="",   # No OCR yet
                media_metadata=media_metadata,
                extraction_notes=notes,
                requires_ocr=True,   # Signal that OCR is needed but deferred
                success=True,
            )

        except Exception as e:
            logger.error(f"Image processing failed for {filename}: {e}")
            return ProcessorResult(
                success=False,
                error=f"Image processing error: {str(e)}\n{traceback.format_exc()}"
            )
