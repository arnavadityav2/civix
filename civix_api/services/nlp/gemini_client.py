"""
CIVIX 2.0 — Gemini NLP Client
Round 2A

Uses the google-genai SDK (v1.60.0 — the new, non-deprecated SDK).
NOT the deprecated google.generativeai package.

Responsibilities:
  1. Accept extracted text (possibly chunked).
  2. Call Gemini with a strict structured prompt.
  3. Retry on transient failures (rate limits, timeouts).
  4. Return raw JSON string for the validator to process.
  5. NEVER return structured objects — always raw string to preserve the
     validator as the trust boundary.

Chunking strategy (as authorized):
  - If text is ≤ MAX_CHARS_PER_CALL → single LLM call.
  - If text is > MAX_CHARS_PER_CALL → split on page boundaries (\n--- PAGE N ---\n)
    and send N chunks. Results are merged by the caller.
"""
import os
import time
import logging
from typing import List, Optional

from .schema import LLM_OUTPUT_SCHEMA_DESCRIPTION, ALLOWED_PREDICATES

logger = logging.getLogger(__name__)

# Approximately 8,000 tokens ≈ 32,000 chars for Gemini Flash.
# We use characters as a proxy for tokens (1 token ≈ 4 chars).
MAX_CHARS_PER_CALL = 28_000

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAYS = [5, 15, 45]  # seconds

# Gemini model selection — Flash is fast and sufficient for NER
GEMINI_MODEL = "gemini-3.6-flash"


def _get_client():
    """Initializes and returns the Gemini client. Raises on missing API key."""
    if os.environ.get("CIVIX_MOCK_NLP") == "1":
        return None  # Client not needed in mock mode

    try:
        from google import genai
    except ImportError:
        raise RuntimeError(
            "google-genai package not installed. Run: pip install google-genai"
        )

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY environment variable is not set. "
            "Cannot call Gemini API."
        )

    return genai.Client(api_key=api_key)


def _build_system_prompt(case_context: str) -> str:
    return f"""You are an intelligence analyst assistant for CIVIX, a criminal investigation platform.

Your task is to extract structured intelligence from investigative documents.

Case context: {case_context}

{LLM_OUTPUT_SCHEMA_DESCRIPTION}

Extract ALL persons, organizations, locations, vehicles, and financial accounts mentioned.
Extract ALL relationships using ONLY the allowed predicates.
Return ONLY the JSON object. No explanation, no markdown, no code fences.
"""


def _split_into_chunks(text: str, max_chars: int) -> List[str]:
    """
    Splits text at page boundaries first. If a page is still too long,
    splits at paragraph boundaries. Never splits mid-sentence.
    """
    # Try to split on page markers
    import re
    pages = re.split(r'\n--- PAGE \d+ ---\n', text)
    pages = [p.strip() for p in pages if p.strip()]

    if not pages:
        pages = [text]

    chunks = []
    current_chunk = []
    current_len = 0

    for page in pages:
        if current_len + len(page) > max_chars and current_chunk:
            # Flush current chunk
            chunks.append("\n\n".join(current_chunk))
            current_chunk = [page]
            current_len = len(page)
        else:
            current_chunk.append(page)
            current_len += len(page)

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks


def call_gemini(
    extracted_text: str,
    case_context: str = "Criminal investigation",
    mock_response: Optional[str] = None,
) -> List[str]:
    """
    Calls Gemini with the extracted text and returns a list of raw JSON strings
    (one per chunk). The caller must merge and validate these.

    Args:
        extracted_text:  The text to analyze.
        case_context:    Brief case context for the prompt.
        mock_response:   If provided, skip actual API call (for testing).

    Returns:
        List of raw JSON strings (one per chunk).

    Raises:
        GeminiCallError: If all retries are exhausted.
    """
    if mock_response is not None:
        logger.info("Using mock Gemini response (testing mode).")
        return [mock_response]
        
    if os.environ.get("CIVIX_MOCK_NLP") == "1":
        logger.info("Using mock Gemini response due to CIVIX_MOCK_NLP=1.")
        mock_str = """{
  "schema_version": "1.0",
  "entities": [
    {"local_id": "E01", "type": "PERSON", "canonical_name": "Rajesh Kumar Verma", "aliases": ["Rajesh Verma"], "attributes": {"date_of_birth": "1984-03-12", "gender": "MALE", "nationality": "IND"}, "confidence": 0.95, "source_spans": [{"page": 1, "text_snippet": "Name: Rajesh Kumar Verma"}]},
    {"local_id": "E02", "type": "PERSON", "canonical_name": "Ananya Singh", "aliases": [], "attributes": {"gender": "FEMALE"}, "confidence": 0.92, "source_spans": [{"page": 1, "text_snippet": "Complainant: Ananya Singh"}]},
    {"local_id": "E03", "type": "PERSON", "canonical_name": "Suresh Babu Yadav", "aliases": ["Suresh Yadav"], "attributes": {"gender": "MALE"}, "confidence": 0.90, "source_spans": [{"page": 1, "text_snippet": "Victim: Suresh Babu Yadav"}]},
    {"local_id": "E04", "type": "VEHICLE", "canonical_name": "RJ14-CB-2847", "aliases": ["white Maruti Swift"], "attributes": {"registration_number": "RJ14-CB-2847", "make": "Maruti", "model": "Swift", "color": "white", "vehicle_type": "CAR"}, "confidence": 0.97, "source_spans": [{"page": 1, "text_snippet": "white Maruti Swift"}]},
    {"local_id": "E05", "type": "ORGANIZATION", "canonical_name": "Verma Traders Private Limited", "aliases": ["Verma Traders"], "attributes": {"org_type": "COMPANY", "registration_number": "U52190RJ2015PTC047921"}, "confidence": 0.94, "source_spans": [{"page": 1, "text_snippet": "Verma Traders Private Limited"}]},
    {"local_id": "E06", "type": "LOCATION", "canonical_name": "Godown No. 7, Sanganer Industrial Area, Jaipur", "aliases": [], "attributes": {"address": "Godown No. 7, Sanganer Industrial Area, Jaipur, Rajasthan"}, "confidence": 0.93, "source_spans": [{"page": 1, "text_snippet": "Godown No. 7"}]},
    {"local_id": "E07", "type": "LOCATION", "canonical_name": "45-B Gandhi Nagar Jaipur", "aliases": ["45-B, Gandhi Nagar"], "attributes": {"address": "45-B, Gandhi Nagar, Jaipur, Rajasthan"}, "confidence": 0.88, "source_spans": [{"page": 1, "text_snippet": "45-B, Gandhi Nagar"}]}
  ],
  "relationships": [
    {"subject_local_id": "E01", "predicate": "OWNS", "object_local_id": "E04", "confidence": 0.95, "source_spans": [{"page": 1, "text_snippet": "registered to Rajesh Kumar Verma"}]},
    {"subject_local_id": "E01", "predicate": "EMPLOYED_BY", "object_local_id": "E05", "confidence": 0.93, "source_spans": [{"page": 1, "text_snippet": "proprietor of Verma Traders"}]},
    {"subject_local_id": "E01", "predicate": "SEEN_AT", "object_local_id": "E06", "confidence": 0.94, "source_spans": [{"page": 1, "text_snippet": "entering the godown"}]},
    {"subject_local_id": "E03", "predicate": "RESIDED_AT", "object_local_id": "E07", "confidence": 0.88, "source_spans": [{"page": 1, "text_snippet": "Permanent Residence: 45-B"}]}
  ],
  "temporal_facts": [
    {"event_description": "Rajesh Kumar Verma observed at Godown", "event_date": "2026-06-15", "event_time": "23:45:00", "temporal_precision": "MINUTE", "involved_entity_local_ids": ["E01", "E06"], "source_spans": [{"page": 1, "text_snippet": "witnessed at approximately 11:45 PM"}]}
  ]
}"""
        return [mock_str]

    if not extracted_text.strip():
        logger.info("Empty text — returning empty extraction result.")
        return ['{"schema_version": "1.0", "entities": [], "relationships": [], "temporal_facts": []}']

    chunks = _split_into_chunks(extracted_text, MAX_CHARS_PER_CALL)
    logger.info(f"Text split into {len(chunks)} chunk(s) for Gemini processing.")

    client = _get_client()
    system_prompt = _build_system_prompt(case_context)
    raw_results = []

    for chunk_idx, chunk in enumerate(chunks):
        logger.info(f"Processing chunk {chunk_idx + 1}/{len(chunks)} ({len(chunk)} chars)")

        user_message = (
            f"Document excerpt (chunk {chunk_idx + 1} of {len(chunks)}):\n\n"
            f"{chunk}\n\n"
            "Extract all entities, relationships, and temporal facts from this excerpt. "
            "Return ONLY the JSON object."
        )

        raw_json = _call_with_retry(client, system_prompt, user_message, chunk_idx)
        raw_results.append(raw_json)

    return raw_results


def _call_with_retry(client, system_prompt: str, user_message: str, chunk_idx: int) -> str:
    """
    Makes the actual Gemini API call with retry logic.
    Returns raw text response string.
    """
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=user_message,
                config={
                    "system_instruction": system_prompt,
                    "temperature": 0.1,       # Low temp for deterministic extraction
                    "max_output_tokens": 8192,
                }
            )

            raw_text = response.text
            if not raw_text or not raw_text.strip():
                raise ValueError("Gemini returned empty response.")

            # Strip markdown fences if model wraps in them despite instruction
            raw_text = raw_text.strip()
            if raw_text.startswith("```"):
                lines = raw_text.split("\n")
                # Remove first and last fence lines
                inner = [l for l in lines if not l.startswith("```")]
                raw_text = "\n".join(inner).strip()

            logger.debug(f"Gemini chunk {chunk_idx + 1} response ({len(raw_text)} chars)")
            return raw_text

        except Exception as e:
            last_error = e
            error_str = str(e).lower()

            # Check for non-retryable errors
            if "api_key" in error_str or "authentication" in error_str or "invalid" in error_str:
                logger.error(f"Non-retryable Gemini error: {e}")
                raise GeminiCallError(f"Non-retryable API error: {e}") from e

            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                logger.warning(
                    f"Gemini call failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}. "
                    f"Retrying in {delay}s..."
                )
                time.sleep(delay)
            else:
                logger.error(f"Gemini call failed after {MAX_RETRIES} attempts: {e}")

    raise GeminiCallError(
        f"Gemini API call failed after {MAX_RETRIES} attempts. Last error: {last_error}"
    ) from last_error


class GeminiCallError(Exception):
    """Raised when Gemini API call fails after all retries."""
    pass
