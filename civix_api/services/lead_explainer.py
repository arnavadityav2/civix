"""
civix_api/services/lead_explainer.py

C3 Gemini Lead Explainer
========================
Provides structured natural-language explanations of investigative leads
using Gemini, constrained to ONLY the deterministic context provided.

DESIGN INVARIANTS:
  - Gemini receives ONLY deterministic findings, paths, entities, events,
    dates, amounts, locations, and provenance.
  - Gemini MUST NOT receive: ground-truth labels, hidden test answers,
    raw database contents, arbitrary graph dumps, or model internals.
  - Gemini's role: EXPLAIN (not DISCOVER, not DECIDE, not CREATE FACTS).
  - All output is validated by LeadValidator before acceptance.
  - If Gemini is unavailable → explanation_status = SKIPPED (fail-safe).
  - Retry policy: 1 retry on transient failure, then SKIPPED.

Output contract (validated JSON):
  {
    "lead_summary": str,             -- 1-2 sentence headline
    "key_evidence": [str, ...],      -- bullet points from findings only
    "investigative_significance": str, -- why this lead matters
    "epistemic_caveats": str,        -- uncertainty/limitations
    "recommended_actions": [str, ...] -- investigative next steps
  }
"""

import json
import logging
import os
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

from civix_api.services.findings_engine import DeterministicFinding

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GEMINI_MODEL = "gemini-3.6-flash"
MAX_RETRIES = 1          # 1 retry — approved by C3 plan
RETRY_DELAY = 10         # seconds between retries
MAX_CONTEXT_CHARS = 8000 # limit context to prevent token blowout

# Expected top-level keys in Gemini explanation response
REQUIRED_EXPLANATION_KEYS = {
    "lead_summary",
    "key_evidence",
    "investigative_significance",
    "epistemic_caveats",
    "recommended_actions",
}


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class ExplanationContext:
    """
    Minimal, deterministic context bundle passed to Gemini.
    Contains ONLY what the deterministic engine has proven.
    """
    subject_name: str
    subject_entity_id: str
    ml_score: float
    findings: List[Dict[str, Any]]    # serialized DeterministicFinding dicts
    # Constrained summary fields (derived from findings, not raw DB)
    entity_names_mentioned: List[str]
    dates_mentioned: List[str]
    amounts_mentioned: List[float]
    locations_mentioned: List[str]
    relationship_types_found: List[str]


@dataclass
class ExplanationResult:
    """Output from the explainer — always valid or a known failure state."""
    status: str               # VALID | SKIPPED | FAILED_VALIDATION
    explanation: Optional[Dict[str, Any]] = None
    raw_response: Optional[str] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Context builder
# ---------------------------------------------------------------------------

def build_explanation_context(
    subject_entity_id: str,
    subject_name: str,
    ml_score: float,
    findings: List[DeterministicFinding],
) -> ExplanationContext:
    """
    Build a constrained context from deterministic findings.
    Extracts only the minimum needed for explanation.
    No raw database values are passed — only structured finding data.
    """
    active_findings = [f for f in findings if not f.suppressed]

    entity_names: List[str] = [subject_name]
    dates: List[str] = []
    amounts: List[float] = []
    locations: List[str] = []
    rel_types: List[str] = []

    serialized = []
    for f in active_findings:
        # Collect entity names from key_facts (already sanitized by engine)
        entity_names.extend([
            fact for fact in f.key_facts
            if len(fact) < 100  # cap length
        ])
        if f.date_range_start:
            dates.append(f.date_range_start[:10])
        if f.date_range_end:
            dates.append(f.date_range_end[:10])
        # Amounts from financial transfers
        if f.finding_type == "FINDING-10-FINANCIAL_TRANSFER" and "total_amount" in f.extra:
            amounts.append(float(f.extra["total_amount"]))
        rel_types.append(f.finding_type)
        serialized.append({
            "finding_type": f.finding_type,
            "relationship_strength": f.relationship_strength,
            "path": f.path_description,
            "key_facts": f.key_facts[:5],  # cap at 5 per finding
            "hop_count": f.hop_count,
        })

    return ExplanationContext(
        subject_entity_id=subject_entity_id,
        subject_name=subject_name,
        ml_score=round(ml_score, 4),
        findings=serialized,
        entity_names_mentioned=list(dict.fromkeys(entity_names))[:20],
        dates_mentioned=list(dict.fromkeys(dates))[:10],
        amounts_mentioned=amounts[:10],
        locations_mentioned=locations[:10],
        relationship_types_found=list(dict.fromkeys(rel_types)),
    )


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _build_explanation_prompt(ctx: ExplanationContext) -> str:
    """
    Build the Gemini prompt. Contains ONLY deterministic context.
    Gemini is instructed explicitly to stay within the provided facts.
    """
    findings_text = json.dumps(ctx.findings, indent=2)
    # Truncate if too long
    if len(findings_text) > MAX_CONTEXT_CHARS:
        findings_text = findings_text[:MAX_CONTEXT_CHARS] + "\n... [truncated for length]"

    return f"""You are an investigative intelligence analyst for CIVIX, a law enforcement investigation platform.

You have been given a set of DETERMINISTIC FINDINGS produced by CIVIX's automated evidence engine.
These findings are factual, source-backed, and auditable.

Your task is to write a structured explanation of why this person has been flagged as an investigative lead.

SUBJECT: {ctx.subject_name} (entity: {ctx.subject_entity_id})
ML ANOMALY SCORE: {ctx.ml_score:.4f} (0=normal, 1=highly anomalous behavioral pattern)

DETERMINISTIC FINDINGS (you must base your explanation ONLY on these):
{findings_text}

STRICT RULES:
1. Do NOT introduce any person, organization, date, amount, or location not present in the findings above.
2. Do NOT make causal claims ("laundered money", "committed fraud") unless explicitly stated in findings.
3. Do NOT speculate about criminal activity beyond what the evidence shows.
4. Use hedged language: "the evidence suggests", "appears to be connected", "warrants investigation".
5. The lead is INVESTIGATIVE, not a conclusion of guilt.

Return ONLY a valid JSON object with exactly these keys:
{{
  "lead_summary": "1-2 sentence headline summarizing the investigative significance",
  "key_evidence": ["fact 1 from findings", "fact 2 from findings", ...],
  "investigative_significance": "Why this combination of signals warrants investigation",
  "epistemic_caveats": "Limitations, uncertainties, or alternative explanations",
  "recommended_actions": ["next investigative step 1", "next investigative step 2", ...]
}}

Return ONLY the JSON. No markdown. No commentary."""


# ---------------------------------------------------------------------------
# Gemini caller
# ---------------------------------------------------------------------------

def _get_gemini_client():
    """Returns Gemini client or None in mock mode."""
    if os.environ.get("CIVIX_MOCK_NLP") == "1":
        return None
    try:
        from google import genai
    except ImportError:
        raise RuntimeError("google-genai package not installed.")
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set.")
    return genai.Client(api_key=api_key)


def _call_gemini_for_explanation(prompt: str, mock_response: Optional[str] = None) -> str:
    """
    Makes the Gemini API call with retry.
    Returns raw response text.
    Raises LeadExplainerError after exhausting retries.
    """
    if mock_response is not None:
        return mock_response

    if os.environ.get("CIVIX_MOCK_NLP") == "1":
        # Return a valid mock explanation in mock mode
        return json.dumps({
            "lead_summary": "Mock explanation: subject has anomalous behavioral signals.",
            "key_evidence": ["Mock finding: communication pattern detected."],
            "investigative_significance": "Behavioral anomaly warrants review.",
            "epistemic_caveats": "This is a mock explanation for testing.",
            "recommended_actions": ["Review communication records."]
        })

    client = _get_gemini_client()
    last_error = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config={
                    "temperature": 0.05,      # Near-deterministic for explanation
                    "max_output_tokens": 2048,
                }
            )
            raw = response.text
            if not raw or not raw.strip():
                raise ValueError("Gemini returned empty response.")

            # Strip markdown fences
            raw = raw.strip()
            if raw.startswith("```"):
                lines = raw.split("\n")
                raw = "\n".join(l for l in lines if not l.startswith("```")).strip()

            logger.debug(f"Gemini explanation response ({len(raw)} chars)")
            return raw

        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            if "api_key" in error_str or "authentication" in error_str:
                raise LeadExplainerError(f"Non-retryable: {e}") from e
            if attempt < MAX_RETRIES:
                logger.warning(f"Gemini explanation failed (attempt {attempt+1}): {e}. Retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"Gemini explanation failed after {MAX_RETRIES+1} attempts: {e}")

    raise LeadExplainerError(f"Exhausted retries. Last error: {last_error}") from last_error


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def explain_lead(
    ctx: ExplanationContext,
    mock_response: Optional[str] = None,
) -> ExplanationResult:
    """
    Generate a validated Gemini explanation for an investigative lead.

    Parameters
    ----------
    ctx : ExplanationContext
        Deterministic context (built by build_explanation_context()).
    mock_response : str, optional
        Override Gemini response for testing.

    Returns
    -------
    ExplanationResult
        Status is one of: VALID (validator accepted), SKIPPED (Gemini unavailable),
        FAILED_VALIDATION (validator rejected).
    """
    if not ctx.findings:
        logger.info(f"No active findings for {ctx.subject_entity_id} — skipping explanation.")
        return ExplanationResult(
            status="SKIPPED",
            error="No active deterministic findings to explain."
        )

    try:
        prompt = _build_explanation_prompt(ctx)
        raw = _call_gemini_for_explanation(prompt, mock_response=mock_response)
    except LeadExplainerError as e:
        logger.warning(f"Gemini unavailable for {ctx.subject_entity_id}: {e}")
        return ExplanationResult(status="SKIPPED", error=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during explanation for {ctx.subject_entity_id}: {e}")
        return ExplanationResult(status="SKIPPED", error=str(e))

    # Validation is done by the caller (LeadValidator) — raw is returned here
    # to preserve the validator as the trust boundary.
    return ExplanationResult(
        status="PENDING_VALIDATION",
        raw_response=raw,
    )


class LeadExplainerError(Exception):
    """Raised when Gemini explanation fails after all retries."""
    pass
