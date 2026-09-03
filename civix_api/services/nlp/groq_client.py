"""
CIVIX 2.0 — Groq NLP Client (Temporary C4 Adapter)
Round 2A

Responsibilities:
  1. Accept extracted text (possibly chunked).
  2. Call Groq with a strict structured prompt.
  3. Retry on transient failures (rate limits, timeouts).
  4. Return raw JSON string for the validator to process.
"""
import os
import time
import logging
from typing import List, Optional
from .schema import LLM_OUTPUT_SCHEMA_DESCRIPTION

logger = logging.getLogger(__name__)

MAX_CHARS_PER_CALL = 28_000
MAX_RETRIES = 3
RETRY_DELAYS = [5, 15, 45]  # seconds

# Use the strongest available model for JSON extraction
GROQ_MODEL = "openai/gpt-oss-120b"


def _get_client():
    if os.environ.get("CIVIX_MOCK_NLP") == "1":
        return None

    try:
        from groq import Groq
    except ImportError:
        raise RuntimeError("groq package not installed. Run: pip install groq")

    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY environment variable is not set. "
            "Cannot call Groq API."
        )

    return Groq(api_key=api_key)


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
            chunks.append("\n\n".join(current_chunk))
            current_chunk = [page]
            current_len = len(page)
        else:
            current_chunk.append(page)
            current_len += len(page)

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks


def call_groq(
    extracted_text: str,
    case_context: str = "Criminal investigation",
    mock_response: Optional[str] = None,
) -> List[str]:
    if mock_response is not None:
        logger.info("Using mock Groq response (testing mode).")
        return [mock_response]
        
    if os.environ.get("CIVIX_MOCK_NLP") == "1":
        logger.info("Using mock Groq response due to CIVIX_MOCK_NLP=1.")
        return ['{"schema_version": "1.0", "entities": [], "relationships": [], "temporal_facts": []}']

    if not extracted_text.strip():
        logger.info("Empty text — returning empty extraction result.")
        return ['{"schema_version": "1.0", "entities": [], "relationships": [], "temporal_facts": []}']

    chunks = _split_into_chunks(extracted_text, MAX_CHARS_PER_CALL)
    logger.info(f"Text split into {len(chunks)} chunk(s) for Groq processing.")

    client = _get_client()
    system_prompt = _build_system_prompt(case_context)
    raw_results = []

    for chunk_idx, chunk in enumerate(chunks):
        logger.info(f"Processing chunk {chunk_idx + 1}/{len(chunks)} ({len(chunk)} chars)")

        user_message = (
            f"Document excerpt (chunk {chunk_idx + 1} of {len(chunks)}):\n\n"
            f"{chunk}\n\n"
            "Extract all entities, relationships, and temporal facts from this excerpt. "
            "Return ONLY the JSON object. Do not wrap it in markdown."
        )

        raw_json = _call_with_retry(client, system_prompt, user_message, chunk_idx)
        raw_results.append(raw_json)

    return raw_results


def _call_with_retry(client, system_prompt: str, user_message: str, chunk_idx: int) -> str:
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )

            raw_text = response.choices[0].message.content
            if not raw_text or not raw_text.strip():
                raise ValueError("Groq returned empty response.")

            raw_text = raw_text.strip()
            if raw_text.startswith("```"):
                lines = raw_text.split("\n")
                inner = [l for l in lines if not l.startswith("```")]
                raw_text = "\n".join(inner).strip()

            logger.debug(f"Groq chunk {chunk_idx + 1} response ({len(raw_text)} chars)")
            return raw_text

        except Exception as e:
            last_error = e
            error_str = str(e).lower()

            if "api_key" in error_str or "authentication" in error_str or "invalid" in error_str:
                logger.error(f"Non-retryable Groq error: {e}")
                raise GroqCallError(f"Non-retryable API error: {e}") from e

            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                logger.warning(
                    f"Groq call failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}. "
                    f"Retrying in {delay}s..."
                )
                time.sleep(delay)
            else:
                logger.error(f"Groq call failed after {MAX_RETRIES} attempts: {e}")

    raise GroqCallError(
        f"Groq API call failed after {MAX_RETRIES} attempts. Last error: {last_error}"
    ) from last_error


class GroqCallError(Exception):
    pass
