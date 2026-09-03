"""
CIVIX 2.0 — Formal Pytest Tests: Evidence Pipeline
Round 2A

Tests the evidence upload, processing, and status API endpoints.

Uses the existing conftest.py infrastructure from tests/api/conftest.py:
  - `client` fixture (AsyncClient via httpx)
  - `admin_headers` fixture (JWT token for admin user)
  - `test_case` fixture (creates a fresh investigative_case)

Run with: pytest tests/api/test_evidence.py -v
"""
import io
import json
import time
import uuid
from typing import Dict

import pytest
import pytest_asyncio
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Minimal synthetic PDF bytes for testing (valid PDF header but minimal content)
# ---------------------------------------------------------------------------
MINIMAL_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n"
    b"4 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 100 700 Td (Test Document) Tj ET\nendstream\nendobj\n"
    b"xref\n0 5\n0000000000 65535 f\n"
    b"trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n9\n%%EOF\n"
)

MINIMAL_TXT = b"Suspect: John Doe. Vehicle: AB12-CD-3456 (blue Toyota Corolla). Location: Main Street, Delhi."

MOCK_NLP_RESPONSE = json.dumps({
    "schema_version": "1.0",
    "entities": [
        {
            "local_id": "E001",
            "type": "PERSON",
            "canonical_name": "John Doe",
            "aliases": [],
            "attributes": {"gender": "MALE"},
            "confidence": 0.90,
            "source_spans": [{"page": None, "text_snippet": "Suspect: John Doe"}]
        },
        {
            "local_id": "E002",
            "type": "VEHICLE",
            "canonical_name": "AB12-CD-3456",
            "aliases": ["blue Toyota Corolla"],
            "attributes": {
                "registration_number": "AB12-CD-3456",
                "make": "Toyota",
                "model": "Corolla",
                "color": "blue",
                "vehicle_type": "CAR"
            },
            "confidence": 0.95,
            "source_spans": [{"page": None, "text_snippet": "Vehicle: AB12-CD-3456"}]
        }
    ],
    "relationships": [
        {
            "subject_local_id": "E001",
            "predicate": "OWNS",
            "object_local_id": "E002",
            "confidence": 0.85,
            "source_spans": [{"page": None, "text_snippet": "Suspect John Doe's vehicle"}]
        }
    ],
    "temporal_facts": []
})


# ---------------------------------------------------------------------------
# Helper: wait for processing status
# ---------------------------------------------------------------------------
async def wait_for_status(
    client: AsyncClient,
    admin_headers: Dict,
    case_id: str,
    artifact_id: str,
    target_statuses: set,
    max_wait: int = 60,
) -> tuple[str, dict]:
    """Poll evidence status endpoint until target status reached."""
    deadline = time.time() + max_wait
    while time.time() < deadline:
        resp = await client.get(
            f"/api/v1/cases/{case_id}/evidence/{artifact_id}",
            headers=admin_headers,
        )
        if resp.status_code == 200:
            body = resp.json()
            status = body.get("processing_status", "")
            if status in target_statuses or status.startswith("FAILED_") or status == "UNSUPPORTED":
                return status, body
        await asyncio.sleep(2)
    return "TIMEOUT", {}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestEvidenceUpload:
    """Tests for POST /cases/{case_id}/evidence/upload"""

    @pytest.mark.asyncio
    async def test_upload_pdf_returns_202(self, client, admin_headers, test_case):
        """Valid PDF upload returns 202 with artifact_id and instance_id."""
        resp = await client.post(
            f"/api/v1/cases/{test_case}/evidence/upload",
            headers=admin_headers,
            files={"file": ("test.pdf", MINIMAL_PDF, "application/pdf")},
            data={"acquisition_method": "FIELD_COLLECTION"},
        )
        assert resp.status_code == 202, f"Expected 202, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert "artifact_id" in body
        assert "instance_id" in body
        assert body["processing_status"] == "STORED"
        assert "pdf" in body.get("mime_type", "").lower()
        assert body["file_size_bytes"] == len(MINIMAL_PDF)

    @pytest.mark.asyncio
    async def test_upload_txt_returns_202(self, client, admin_headers, test_case):
        """Plain text upload returns 202."""
        resp = await client.post(
            f"/api/v1/cases/{test_case}/evidence/upload",
            headers=admin_headers,
            files={"file": ("intel.txt", MINIMAL_TXT, "text/plain")},
            data={"acquisition_method": "INTELLIGENCE"},
        )
        assert resp.status_code == 202
        body = resp.json()
        assert body["processing_status"] == "STORED"

    @pytest.mark.asyncio
    async def test_upload_empty_file_rejected(self, client, admin_headers, test_case):
        """Empty file is rejected with 400."""
        resp = await client.post(
            f"/api/v1/cases/{test_case}/evidence/upload",
            headers=admin_headers,
            files={"file": ("empty.pdf", b"", "application/pdf")},
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_requires_auth(self, client, test_case):
        """Unauthenticated upload is rejected with 401."""
        resp = await client.post(
            f"/api/v1/cases/{test_case}/evidence/upload",
            files={"file": ("test.pdf", MINIMAL_PDF, "application/pdf")},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_upload_unknown_case_returns_404(self, client, admin_headers):
        """Upload to non-existent case returns 404."""
        fake_case = str(uuid.uuid4())
        resp = await client.post(
            f"/api/v1/cases/{fake_case}/evidence/upload",
            headers=admin_headers,
            files={"file": ("test.pdf", MINIMAL_PDF, "application/pdf")},
        )
        # Should be 403 (no case_access) or 404 (case not found)
        assert resp.status_code in (403, 404)

    @pytest.mark.asyncio
    async def test_duplicate_file_rejected(self, client, admin_headers, test_case):
        """Uploading the same file twice to the same case returns 409."""
        unique_content = f"unique evidence {uuid.uuid4()}".encode()
        
        # First upload
        resp1 = await client.post(
            f"/api/v1/cases/{test_case}/evidence/upload",
            headers=admin_headers,
            files={"file": ("dup_test.txt", unique_content, "text/plain")},
        )
        assert resp1.status_code == 202
        
        # Second upload — same content, same case
        resp2 = await client.post(
            f"/api/v1/cases/{test_case}/evidence/upload",
            headers=admin_headers,
            files={"file": ("dup_test.txt", unique_content, "text/plain")},
        )
        assert resp2.status_code == 409, f"Expected 409 for duplicate, got {resp2.status_code}: {resp2.text}"


class TestEvidenceStatus:
    """Tests for GET /cases/{case_id}/evidence and GET /cases/{case_id}/evidence/{artifact_id}"""

    @pytest.mark.asyncio
    async def test_list_evidence_returns_200(self, client, admin_headers, test_case):
        """List evidence returns 200 with an array."""
        resp = await client.get(
            f"/api/v1/cases/{test_case}/evidence",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.asyncio
    async def test_get_evidence_status(self, client, admin_headers, test_case):
        """Get specific evidence returns processing_status."""
        # First upload something
        unique_content = f"status test {uuid.uuid4()}".encode()
        upload_resp = await client.post(
            f"/api/v1/cases/{test_case}/evidence/upload",
            headers=admin_headers,
            files={"file": ("status_test.txt", unique_content, "text/plain")},
        )
        assert upload_resp.status_code == 202
        artifact_id = upload_resp.json()["artifact_id"]
        
        # Get status
        status_resp = await client.get(
            f"/api/v1/cases/{test_case}/evidence/{artifact_id}",
            headers=admin_headers,
        )
        assert status_resp.status_code == 200
        body = status_resp.json()
        assert "processing_status" in body
        assert body["processing_status"] in (
            "STORED", "PENDING", "PROCESSING", "TEXT_EXTRACTED",
            "NLP_ANALYZED", "COMPLETED", "FAILED_EXTRACTION",
            "FAILED_NLP", "FAILED_MAPPING", "UNSUPPORTED"
        )

    @pytest.mark.asyncio
    async def test_get_nonexistent_evidence_returns_404(self, client, admin_headers, test_case):
        """Getting non-existent artifact returns 404."""
        fake_id = str(uuid.uuid4())
        resp = await client.get(
            f"/api/v1/cases/{test_case}/evidence/{fake_id}",
            headers=admin_headers,
        )
        assert resp.status_code == 404


class TestNLPValidation:
    """Tests for the NLP validator layer (unit tests, no DB needed)."""

    def test_valid_extraction_passes(self):
        """Well-formed LLM output passes validation."""
        from civix_api.services.nlp.validator import validate
        result = validate(MOCK_NLP_RESPONSE)
        assert len(result.entities) == 2
        assert len(result.relationships) == 1
        assert len(result.temporal_facts) == 0

    def test_malformed_json_raises(self):
        """Unparseable JSON raises NLPValidationError."""
        from civix_api.services.nlp.validator import validate, NLPValidationError
        with pytest.raises(NLPValidationError):
            validate("not json at all {{{")

    def test_missing_schema_version_raises(self):
        """Missing schema_version raises NLPValidationError."""
        from civix_api.services.nlp.validator import validate, NLPValidationError
        with pytest.raises(NLPValidationError):
            validate(json.dumps({"entities": [], "relationships": [], "temporal_facts": []}))

    def test_invalid_predicate_dropped(self):
        """Invalid predicate is dropped, not raised."""
        from civix_api.services.nlp.validator import validate
        raw = json.dumps({
            "schema_version": "1.0",
            "entities": [{
                "local_id": "E001", "type": "PERSON", "canonical_name": "Test Person",
                "aliases": [], "attributes": {}, "confidence": 0.9,
                "source_spans": []
            }],
            "relationships": [{
                "subject_local_id": "E001", "predicate": "INVENTED_PREDICATE",
                "object_local_id": "E001", "confidence": 0.9, "source_spans": []
            }],
            "temporal_facts": []
        })
        result = validate(raw)
        assert len(result.relationships) == 0
        assert len(result.validation_warnings) > 0

    def test_low_confidence_entity_filtered(self):
        """Entity below confidence threshold is filtered out."""
        from civix_api.services.nlp.validator import validate
        raw = json.dumps({
            "schema_version": "1.0",
            "entities": [{
                "local_id": "E001", "type": "PERSON", "canonical_name": "Low Conf",
                "aliases": [], "attributes": {}, "confidence": 0.1,
                "source_spans": []
            }],
            "relationships": [],
            "temporal_facts": []
        })
        result = validate(raw)
        assert len(result.entities) == 0

    def test_empty_canonical_name_filtered(self):
        """Entity with empty canonical_name is filtered out."""
        from civix_api.services.nlp.validator import validate
        raw = json.dumps({
            "schema_version": "1.0",
            "entities": [{
                "local_id": "E001", "type": "PERSON", "canonical_name": "",
                "aliases": [], "attributes": {}, "confidence": 0.9,
                "source_spans": []
            }],
            "relationships": [],
            "temporal_facts": []
        })
        result = validate(raw)
        assert len(result.entities) == 0

    def test_unknown_entity_type_filtered(self):
        """Entity with unknown type is filtered out."""
        from civix_api.services.nlp.validator import validate
        raw = json.dumps({
            "schema_version": "1.0",
            "entities": [{
                "local_id": "E001", "type": "PLANET", "canonical_name": "Mars",
                "aliases": [], "attributes": {}, "confidence": 0.9,
                "source_spans": []
            }],
            "relationships": [],
            "temporal_facts": []
        })
        result = validate(raw)
        assert len(result.entities) == 0

    def test_duplicate_local_id_dropped(self):
        """Duplicate local_id: second occurrence is dropped."""
        from civix_api.services.nlp.validator import validate
        raw = json.dumps({
            "schema_version": "1.0",
            "entities": [
                {"local_id": "E001", "type": "PERSON", "canonical_name": "Person A",
                 "aliases": [], "attributes": {}, "confidence": 0.9, "source_spans": []},
                {"local_id": "E001", "type": "PERSON", "canonical_name": "Person B",
                 "aliases": [], "attributes": {}, "confidence": 0.9, "source_spans": []},
            ],
            "relationships": [],
            "temporal_facts": []
        })
        result = validate(raw)
        assert len(result.entities) == 1
        assert result.entities[0].canonical_name == "Person A"


class TestTextProcessors:
    """Tests for the processor layer (unit tests, no API)."""

    def test_pdf_processor_extracts_text(self):
        """PDFProcessor extracts text from a valid PDF."""
        from civix_api.services.processors.pdf_processor import PDFProcessor
        processor = PDFProcessor()
        result = processor.process(MINIMAL_PDF, "application/pdf", "test.pdf")
        assert result.success
        assert result.page_count >= 1
        assert result.media_metadata["extraction_method"] == "pymupdf_text"

    def test_text_processor_handles_plain_text(self):
        """TextProcessor handles plain text content."""
        from civix_api.services.processors.text_processor import TextProcessor
        processor = TextProcessor()
        result = processor.process(MINIMAL_TXT, "text/plain", "test.txt")
        assert result.success
        assert result.extracted_text == MINIMAL_TXT.decode("utf-8", errors="replace")

    def test_resolver_dispatches_pdf(self):
        """ProcessorResolver dispatches PDF to PDFProcessor."""
        from civix_api.services.processors.resolver import ProcessorResolver
        mime, result = ProcessorResolver.resolve(MINIMAL_PDF, "test.pdf")
        assert mime == "application/pdf"
        assert result.success

    def test_resolver_rejects_empty_file(self):
        """ProcessorResolver rejects empty file."""
        from civix_api.services.processors.resolver import ProcessorResolver
        mime, result = ProcessorResolver.resolve(b"", "test.pdf")
        assert not result.success

    def test_resolver_returns_unsupported_for_unknown_mime(self):
        """ProcessorResolver returns UNSUPPORTED for binary blob."""
        from civix_api.services.processors.resolver import ProcessorResolver
        # Random binary data that doesn't match any MIME magic bytes
        binary_blob = bytes(range(256))
        mime, result = ProcessorResolver.resolve(binary_blob, "data.xyz")
        assert not result.success
        assert "Unsupported file type" in (result.error or "")


class TestEvidenceStore:
    """Tests for evidence_store.py (unit tests, no DB/API)."""

    def test_store_and_retrieve(self, tmp_path):
        """Stores a file and retrieves it by storage_uri."""
        import os
        os.environ["CIVIX_EVIDENCE_STORE_PATH"] = str(tmp_path)
        
        from civix_api.services.evidence_store import store_file, retrieve_file
        
        content = b"test evidence content"
        uri, sha256, is_dup = store_file(content, "test.txt")
        assert not is_dup
        assert uri.startswith("local://civix_evidence_store/")
        
        retrieved = retrieve_file(uri)
        assert retrieved == content
        
        del os.environ["CIVIX_EVIDENCE_STORE_PATH"]

    def test_duplicate_detection(self, tmp_path):
        """Same content stored twice returns is_duplicate=True on second call."""
        import os
        os.environ["CIVIX_EVIDENCE_STORE_PATH"] = str(tmp_path)
        
        from civix_api.services.evidence_store import store_file
        
        content = b"duplicate test"
        _, _, dup1 = store_file(content, "dup.txt")
        _, _, dup2 = store_file(content, "dup.txt")
        assert not dup1
        assert dup2
        
        del os.environ["CIVIX_EVIDENCE_STORE_PATH"]

    def test_retrieve_nonexistent_raises(self, tmp_path):
        """Retrieving non-existent file raises FileNotFoundError."""
        import os
        os.environ["CIVIX_EVIDENCE_STORE_PATH"] = str(tmp_path)
        
        from civix_api.services.evidence_store import retrieve_file
        
        with pytest.raises(FileNotFoundError):
            retrieve_file("local://civix_evidence_store/0000/nonexistent/file.txt")
        
        del os.environ["CIVIX_EVIDENCE_STORE_PATH"]

    def test_sanitize_filename(self):
        """Sanitize filename strips path traversal and unsafe chars."""
        from civix_api.services.evidence_store import sanitize_filename
        assert sanitize_filename("../../../etc/passwd") == "passwd"
        assert sanitize_filename("my file.pdf") == "my_file.pdf"
        assert sanitize_filename("report-2026.pdf") == "report-2026.pdf"


# ---------------------------------------------------------------------------
# Import asyncio for wait helper
# ---------------------------------------------------------------------------
import asyncio
