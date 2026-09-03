"""
CIVIX 2.0 — PDF Processor (PyMuPDF)
Round 2A

Uses PyMuPDF (fitz) which is already installed (v1.28.0).
No Poppler or pdfplumber dependency required.

Text extraction strategy:
  1. Open PDF with PyMuPDF.
  2. Extract text from each page with page-boundary markers.
  3. If total usable text < 50 chars after stripping → set requires_ocr=True.
     (OCR itself is deferred to Round 2B when Tesseract is installed.)
  4. Store page_count and PDF metadata in media_metadata.
"""
import logging
from typing import Optional
import traceback

from .base import BaseProcessor, ProcessorResult

logger = logging.getLogger(__name__)

# Threshold below which a PDF is considered likely scanned (no text layer)
_MIN_USABLE_TEXT_CHARS = 50


class PDFProcessor(BaseProcessor):
    SUPPORTED_MIME_TYPES = ["application/pdf"]

    def process(self, file_bytes: bytes, mime_type: str, filename: str) -> ProcessorResult:
        try:
            import fitz  # PyMuPDF
        except ImportError:
            return ProcessorResult(
                success=False,
                error="PyMuPDF (fitz) is not installed. Cannot process PDF."
            )

        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")

            page_count = doc.page_count
            all_text_parts = []

            for page_num in range(page_count):
                page = doc[page_num]
                page_text = page.get_text("text")
                if page_text.strip():
                    all_text_parts.append(f"--- PAGE {page_num + 1} ---\n{page_text}")

            doc.close()

            full_text = "\n".join(all_text_parts)
            usable_chars = len(full_text.strip())

            requires_ocr = usable_chars < _MIN_USABLE_TEXT_CHARS

            notes = []
            if requires_ocr:
                notes.append(
                    f"PDF appears to be scanned or image-only (only {usable_chars} usable chars). "
                    "OCR deferred to Round 2B."
                )
            else:
                notes.append(f"Text extracted: {usable_chars} chars across {page_count} page(s).")

            media_metadata = {
                "page_count": page_count,
                "extraction_method": "pymupdf_text",
                "usable_chars": usable_chars,
                "requires_ocr": requires_ocr,
            }

            return ProcessorResult(
                extracted_text=full_text,
                page_count=page_count,
                media_metadata=media_metadata,
                extraction_notes=" ".join(notes),
                requires_ocr=requires_ocr,
                success=True,
            )

        except Exception as e:
            logger.error(f"PDF processing failed for {filename}: {e}")
            return ProcessorResult(
                success=False,
                error=f"PDF processing error: {str(e)}\n{traceback.format_exc()}"
            )
