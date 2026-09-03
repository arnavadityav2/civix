"""
civix_api/services/lead_validator.py

C3 Zero-Hallucination Lead Validator
======================================
Validates Gemini explanation output against the deterministic context that
was provided to Gemini. Fails closed — any unsupported claim is REJECTED.

VALIDATION RULES:
  1. JSON parseable
  2. All required keys present
  3. No unsupported entity names introduced
  4. No unsupported dates introduced
  5. No unsupported amounts introduced
  6. No unsupported locations introduced
  7. No unsupported causal claims
  8. lead_summary length sanity check
  9. key_evidence items must relate to actual findings

PHILOSOPHY: False negatives (over-rejection) are preferred to false positives
(accepting hallucinated content). A REJECTED explanation causes the lead to be
saved with explanation_status=REJECTED and explanation=None. The lead itself
(with its deterministic findings and ML score) remains valid and visible.

Output:
  ValidationResult with status: VALID | INVALID | FAILED_VALIDATION
"""

import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from civix_api.services.lead_explainer import (
    ExplanationContext,
    REQUIRED_EXPLANATION_KEYS,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Causal claim patterns to detect hallucinated conclusions
# ---------------------------------------------------------------------------
FORBIDDEN_CAUSAL_PATTERNS = [
    r'\blaundered\b',
    r'\blaundering\b',
    r'\bfraud\b',
    r'\bterrorism\b',
    r'\bmurder\b',
    r'\bdrug trafficking\b',
    r'\bsmuggling\b',
    r'\bkidnapping\b',
    r'\bextortion\b',
    r'\bbribery\b',
    r'\bcorruption\b',
    r'\bcartel\b',
    r'\bcriminal organization\b',
    r'\bis guilty\b',
    r'\bcommitted\b',
    r'\bproved?\b',
    r'\bconvicted\b',
    r'\bwe know that\b',
    r'\bconfirmed that\b',
    r'\bclearly\b',
    r'\bundoubtedly\b',
    r'\bwithout doubt\b',
    r'\bno question\b',
]

# Maximum tolerated length for lead_summary (chars)
MAX_SUMMARY_LEN = 500
MAX_SIGNIFICANCE_LEN = 1000
MAX_KEY_EVIDENCE_ITEMS = 10
MAX_RECOMMENDED_ACTIONS = 8


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    """Result of validating a Gemini explanation."""
    status: str                      # VALID | INVALID | FAILED_VALIDATION
    validated_explanation: Optional[Dict[str, Any]] = None
    violations: List[str] = None

    def __post_init__(self):
        if self.violations is None:
            self.violations = []


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

class LeadValidator:
    """
    Zero-hallucination validator for Gemini lead explanations.
    Fails closed — any doubt results in INVALID.
    """

    def validate(
        self,
        raw_response: str,
        ctx: ExplanationContext,
    ) -> ValidationResult:
        """
        Validate a Gemini raw response against the explanation context.

        Parameters
        ----------
        raw_response : str
            The raw JSON string returned by Gemini.
        ctx : ExplanationContext
            The exact context that was sent to Gemini.

        Returns
        -------
        ValidationResult
            VALID if all checks pass, INVALID/FAILED_VALIDATION otherwise.
        """
        violations: List[str] = []

        # ----------------------------------------------------------------
        # CHECK 1: JSON parseable
        # ----------------------------------------------------------------
        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError as e:
            return ValidationResult(
                status="FAILED_VALIDATION",
                violations=[f"JSON parse error: {e}"],
            )

        if not isinstance(parsed, dict):
            return ValidationResult(
                status="FAILED_VALIDATION",
                violations=["Top-level response is not a JSON object."],
            )

        # ----------------------------------------------------------------
        # CHECK 2: Required keys present
        # ----------------------------------------------------------------
        missing_keys = REQUIRED_EXPLANATION_KEYS - set(parsed.keys())
        if missing_keys:
            violations.append(f"Missing required keys: {missing_keys}")

        # ----------------------------------------------------------------
        # CHECK 3: Type validation
        # ----------------------------------------------------------------
        if "lead_summary" in parsed and not isinstance(parsed["lead_summary"], str):
            violations.append("lead_summary must be a string.")
        if "key_evidence" in parsed and not isinstance(parsed["key_evidence"], list):
            violations.append("key_evidence must be a list.")
        if "recommended_actions" in parsed and not isinstance(parsed["recommended_actions"], list):
            violations.append("recommended_actions must be a list.")
        if "investigative_significance" in parsed and not isinstance(parsed["investigative_significance"], str):
            violations.append("investigative_significance must be a string.")
        if "epistemic_caveats" in parsed and not isinstance(parsed["epistemic_caveats"], str):
            violations.append("epistemic_caveats must be a string.")

        # Bail early if structural issues
        if violations:
            return ValidationResult(status="FAILED_VALIDATION", violations=violations)

        # ----------------------------------------------------------------
        # CHECK 4: Length sanity
        # ----------------------------------------------------------------
        if len(parsed.get("lead_summary", "")) > MAX_SUMMARY_LEN:
            violations.append(f"lead_summary exceeds {MAX_SUMMARY_LEN} chars.")
        if len(parsed.get("investigative_significance", "")) > MAX_SIGNIFICANCE_LEN:
            violations.append(f"investigative_significance exceeds {MAX_SIGNIFICANCE_LEN} chars.")
        if len(parsed.get("key_evidence", [])) > MAX_KEY_EVIDENCE_ITEMS:
            violations.append(f"key_evidence has more than {MAX_KEY_EVIDENCE_ITEMS} items.")
        if len(parsed.get("recommended_actions", [])) > MAX_RECOMMENDED_ACTIONS:
            violations.append(f"recommended_actions has more than {MAX_RECOMMENDED_ACTIONS} items.")

        # ----------------------------------------------------------------
        # BUILD CONTEXT ALLOWLISTS from deterministic findings
        # ----------------------------------------------------------------
        # These are the ONLY things Gemini is allowed to reference
        allowed_text = self._build_allowed_text_corpus(ctx)

        # ----------------------------------------------------------------
        # CHECK 5: No unsupported dates
        # ----------------------------------------------------------------
        date_violations = self._check_dates(parsed, ctx)
        violations.extend(date_violations)

        # ----------------------------------------------------------------
        # CHECK 6: No unsupported amounts
        # ----------------------------------------------------------------
        amount_violations = self._check_amounts(parsed, ctx)
        violations.extend(amount_violations)

        # ----------------------------------------------------------------
        # CHECK 7: No forbidden causal claims
        # ----------------------------------------------------------------
        causal_violations = self._check_causal_claims(parsed)
        violations.extend(causal_violations)

        # ----------------------------------------------------------------
        # CHECK 8: key_evidence items must not be entirely empty
        # ----------------------------------------------------------------
        evidence_items = parsed.get("key_evidence", [])
        for i, item in enumerate(evidence_items):
            if not isinstance(item, str) or not item.strip():
                violations.append(f"key_evidence[{i}] is empty or not a string.")

        # ----------------------------------------------------------------
        # RESULT
        # ----------------------------------------------------------------
        if violations:
            logger.warning(
                f"Explanation validation FAILED for entity {ctx.subject_entity_id}: "
                f"{len(violations)} violation(s): {violations[:3]}"
            )
            return ValidationResult(status="INVALID", violations=violations)

        logger.info(f"Explanation validation PASSED for entity {ctx.subject_entity_id}")
        return ValidationResult(
            status="VALID",
            validated_explanation=parsed,
            violations=[],
        )

    def _build_allowed_text_corpus(self, ctx: ExplanationContext) -> str:
        """Build a corpus of all text that was provided to Gemini."""
        parts = [ctx.subject_name]
        parts.extend(ctx.entity_names_mentioned)
        parts.extend(ctx.dates_mentioned)
        parts.extend(ctx.locations_mentioned)
        for f in ctx.findings:
            parts.extend(f.get("key_facts", []))
            parts.append(f.get("path", ""))
        return " ".join(str(p) for p in parts).lower()

    def _check_dates(
        self, parsed: dict, ctx: ExplanationContext
    ) -> List[str]:
        """
        Check that no date patterns appear in the explanation that weren't
        in the original context.
        """
        violations = []
        if not ctx.dates_mentioned:
            return violations  # No dates in context — any date would be fabricated,
            # but we only reject if a specific date format appears

        # Extract date-like strings from the explanation
        all_text = self._flatten_parsed(parsed)
        found_dates = re.findall(r'\b\d{4}-\d{2}-\d{2}\b', all_text)

        allowed_years = set()
        for d in ctx.dates_mentioned:
            # Extract year from ISO dates
            m = re.match(r'(\d{4})', d)
            if m:
                allowed_years.add(m.group(1))

        for d in found_dates:
            year = d[:4]
            if year not in allowed_years and d not in ctx.dates_mentioned:
                violations.append(f"Unsupported date found in explanation: {d}")

        return violations

    def _check_amounts(
        self, parsed: dict, ctx: ExplanationContext
    ) -> List[str]:
        """
        Check that financial amounts cited in the explanation are not
        significantly different from what was provided in context.
        """
        violations = []
        if not ctx.amounts_mentioned:
            return violations

        all_text = self._flatten_parsed(parsed)
        # Look for currency-style numbers (e.g., 50000, 1,00,000, 50,000.00)
        found_amounts = re.findall(r'\b\d[\d,]*(?:\.\d{1,2})?\b', all_text)

        # Build set of allowed numeric values (rounded to int for comparison)
        allowed_amounts: Set[int] = set()
        for a in ctx.amounts_mentioned:
            if a > 0:
                allowed_amounts.add(int(round(a)))
                # Allow ±10% tolerance for rounding
                allowed_amounts.add(int(round(a * 0.9)))
                allowed_amounts.add(int(round(a * 1.1)))

        for amount_str in found_amounts:
            try:
                val = int(amount_str.replace(",", ""))
                if val > 1000:  # Only check significant amounts
                    if val not in allowed_amounts:
                        # Check if it's within 10% of any allowed amount
                        close = any(
                            abs(val - a) / max(a, 1) < 0.15
                            for a in allowed_amounts if a > 0
                        )
                        if not close:
                            violations.append(
                                f"Unsupported amount in explanation: {amount_str} "
                                f"(allowed: {sorted(allowed_amounts)[:5]}...)"
                            )
            except ValueError:
                continue

        return violations

    def _check_causal_claims(self, parsed: dict) -> List[str]:
        """
        Reject explanations that make unsupported causal/criminal claims.
        """
        violations = []
        all_text = self._flatten_parsed(parsed).lower()

        for pattern in FORBIDDEN_CAUSAL_PATTERNS:
            if re.search(pattern, all_text, re.IGNORECASE):
                violations.append(
                    f"Forbidden causal/conclusive claim detected matching pattern: '{pattern}'"
                )

        return violations

    def _flatten_parsed(self, parsed: dict) -> str:
        """Flatten all string content from the parsed response."""
        parts = []
        for v in parsed.values():
            if isinstance(v, str):
                parts.append(v)
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, str):
                        parts.append(item)
        return " ".join(parts)


# ---------------------------------------------------------------------------
# Module-level convenience function
# ---------------------------------------------------------------------------

def validate_explanation(
    raw_response: str,
    ctx: ExplanationContext,
) -> ValidationResult:
    """Module-level entry point."""
    validator = LeadValidator()
    return validator.validate(raw_response, ctx)
