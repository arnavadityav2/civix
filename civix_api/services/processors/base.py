"""
CIVIX 2.0 — Processor Base Types
Round 2A

Defines the ProcessorResult dataclass and BaseProcessor interface.
All format-specific processors must implement BaseProcessor.process().
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class ProcessorResult:
    """
    Returned by every processor.

    extracted_text  — raw text content (may be empty string, never None for text/pdf)
    page_count      — number of pages (PDF only; None for other types)
    media_metadata  — format-specific metadata stored in evidence_artifact.media_metadata
    extraction_notes — human-readable notes about extraction quality
    requires_ocr    — True if text layer was absent and OCR would help (deferred to Round 2B)
    success         — False if the processor encountered a fatal error
    error           — Error message if success=False
    """
    extracted_text: str = ""
    page_count: Optional[int] = None
    media_metadata: Dict[str, Any] = field(default_factory=dict)
    extraction_notes: str = ""
    requires_ocr: bool = False
    success: bool = True
    error: Optional[str] = None


class BaseProcessor:
    """
    Abstract base class for all evidence processors.
    Subclasses must implement the `process` method.
    """
    SUPPORTED_MIME_TYPES: list[str] = []

    def process(self, file_bytes: bytes, mime_type: str, filename: str) -> ProcessorResult:
        raise NotImplementedError(f"{self.__class__.__name__} must implement process()")
