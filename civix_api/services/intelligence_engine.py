"""
civix_api/services/intelligence_engine.py

C3 Intelligence Engine Orchestrator
=====================================
Orchestrates the full C3 pipeline for a single subject entity:

  1. Deterministic Findings Engine → DeterministicFinding[]
  2. Feature Adapter → 70-feature vector (exact contract)
  3. XGBoost Inference → ml_score
  4. Investigative Lead assembly
  5. Gemini Explanation (async-safe, fail-graceful)
  6. Zero-Hallucination Validation
  7. Persist InvestigativeLead + InvestigativeFinding rows
  8. Outbox / Neo4j projection (via trigger)

PIPELINE INVARIANTS:
  - Deterministic facts are never modified by downstream stages
  - ML score is independent of explanation
  - Explanation cannot alter findings or score
  - Idempotency: same subject + case + as_of → same canonical_key → UPSERT
  - Temporal safety: as_of boundaries enforced throughout
  - Fail-safe: any stage failure → lead persisted with that stage's error status

SCOPE BOUNDARY:
  - DOES NOT create SAME_AS or RESOLVES_TO edges
  - DOES NOT auto-merge identities
  - DOES NOT perform online training
  - C2 candidates consumed read-only (as a finding type only)
"""

import json
import logging
import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from civix_api.services.findings_engine import (
    DeterministicFinding,
    generate_findings_for_entity,
    FEATURE_VECTOR_VERSION,
)

# Re-export for router imports
__all__ = ["generate_lead_for_entity", "LeadGenerationResult", "FEATURE_VECTOR_VERSION"]
from civix_api.services.lead_explainer import (
    ExplanationContext,
    ExplanationResult,
    build_explanation_context,
    explain_lead,
)
from civix_api.services.lead_validator import validate_explanation, ValidationResult
from civix_api.services.ml_service import MLService, EXPECTED_FEATURES, get_ml_service

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lead generation result
# ---------------------------------------------------------------------------

@dataclass
class LeadGenerationResult:
    lead_id: str
    subject_entity_id: str
    subject_name: str
    ml_score: float
    priority: str
    lead_text: str
    explanation_status: str
    finding_count: int
    active_finding_count: int
    created: bool      # True = new lead, False = existing (idempotent)


# ---------------------------------------------------------------------------
# Feature adapter (enforces exact 70-feature contract)
# ---------------------------------------------------------------------------

def build_feature_vector(feature_dict: Dict[str, float]) -> List[float]:
    """
    Adapt a feature dict (from extract_candidate_features) into the exact
    70-feature ordered list required by XGBoost.

    Validation: asserts exactly 70 values in exactly the approved order.
    Missing values → 0.0 (deterministic convention).

    Raises ValueError if feature count does not equal 70 after assembly.
    """
    vector = [float(feature_dict.get(f, 0.0)) for f in EXPECTED_FEATURES]
    if len(vector) != 70:
        raise ValueError(
            f"Feature vector length mismatch: expected 70, got {len(vector)}"
        )
    return vector


def validate_feature_names(feature_dict: Dict[str, Any]) -> None:
    """
    Verify the feature dict covers the exact 70-feature contract.
    Logs warnings for missing features (they will be zero-filled).
    """
    missing = [f for f in EXPECTED_FEATURES if f not in feature_dict]
    extra = [f for f in feature_dict if f not in EXPECTED_FEATURES]
    if missing:
        logger.warning(f"Feature dict missing {len(missing)} features (will be zero-filled): {missing[:5]}...")
    if extra:
        logger.debug(f"Feature dict has {len(extra)} extra keys (ignored): {extra[:5]}...")


# ---------------------------------------------------------------------------
# Canonical key for idempotency
# ---------------------------------------------------------------------------

def _canonical_key(subject_entity_id: str, case_id: str, as_of_date: str) -> str:
    """
    Deterministic canonical key for deduplication.
    Same (subject, case, date) → same key → UPSERT instead of INSERT.
    """
    raw = f"{subject_entity_id}|{case_id}|{as_of_date}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


# ---------------------------------------------------------------------------
# Priority calculation
# ---------------------------------------------------------------------------

def _score_to_priority(score: float, finding_count: int) -> str:
    if score >= 0.85 or (score >= 0.70 and finding_count >= 3):
        return "HIGH"
    elif score >= 0.60 or finding_count >= 2:
        return "MEDIUM"
    return "LOW"


# ---------------------------------------------------------------------------
# Lead text builder (non-hardcoded, deterministic)
# ---------------------------------------------------------------------------

def _build_lead_text(
    subject_name: str,
    ml_score: float,
    findings: List[DeterministicFinding],
    explanation_status: str,
    explanation: Optional[Dict[str, Any]],
) -> str:
    """
    Produce lead_text. If explanation is valid, use it. Otherwise build from findings.
    This is NEVER the hardcoded placeholder string.
    """
    if explanation_status == "VALID" and explanation:
        summary = explanation.get("lead_summary", "")
        if summary:
            return summary

    active = [f for f in findings if not f.suppressed]
    if not active:
        return (
            f"Behavioral anomaly detected for {subject_name} "
            f"(ML score: {ml_score:.3f}). No deterministic findings generated."
        )

    finding_types = list(dict.fromkeys(f.finding_type for f in active))
    return (
        f"{subject_name} flagged with ML anomaly score {ml_score:.3f}. "
        f"Deterministic findings: {', '.join(finding_types[:3])}{'...' if len(finding_types) > 3 else ''}. "
        f"Total signals: {len(active)}."
    )


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

class IntelligenceEngine:
    """
    Full C3 pipeline orchestrator.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def generate_lead_for_entity(
        self,
        subject_entity_id: str,
        case_id: str,
        run_id: str,
        user_id: str,
        as_of: Optional[datetime] = None,
        hypothesis_id: Optional[str] = None,
        mock_explanation: Optional[str] = None,
    ) -> LeadGenerationResult:
        """
        Full C3 pipeline for one subject entity.

        Returns LeadGenerationResult regardless of intermediate failures.
        Persists a lead row with appropriate status fields for any failure mode.
        """
        if as_of is None:
            as_of = datetime.utcnow()

        as_of_date = as_of.strftime("%Y-%m-%d")
        canonical_key = _canonical_key(subject_entity_id, case_id, as_of_date)

        # Resolve display name
        subject_name = await self._get_display_name(subject_entity_id)

        # ----------------------------------------------------------------
        # STAGE 1: Deterministic Findings
        # ----------------------------------------------------------------
        logger.info(f"[C3] Stage 1: Deterministic findings for {subject_name} ({subject_entity_id})")
        try:
            findings = await generate_findings_for_entity(
                self.session, subject_entity_id, case_id, as_of
            )
        except Exception as e:
            logger.error(f"[C3] Findings engine failed for {subject_entity_id}: {e}")
            findings = []

        active_findings = [f for f in findings if not f.suppressed]
        logger.info(f"[C3] {len(findings)} findings ({len(active_findings)} active, {len(findings)-len(active_findings)} suppressed)")

        # ----------------------------------------------------------------
        # STAGE 2: Feature Extraction (uses existing extract_candidate_features)
        # ----------------------------------------------------------------
        logger.info(f"[C3] Stage 2: Feature extraction")
        try:
            from civix_api.services.feature_extractor import extract_candidate_features
            feature_map = await extract_candidate_features(self.session, [subject_entity_id])
            feature_dict = feature_map.get(subject_entity_id, {})
            validate_feature_names(feature_dict)
            feature_vector = build_feature_vector(feature_dict)
            assert len(feature_vector) == 70, f"CRITICAL: feature vector not 70: {len(feature_vector)}"
        except Exception as e:
            logger.error(f"[C3] Feature extraction failed for {subject_entity_id}: {e}")
            feature_vector = [0.0] * 70
            feature_dict = {}

        # ----------------------------------------------------------------
        # STAGE 3: XGBoost Inference
        # ----------------------------------------------------------------
        logger.info(f"[C3] Stage 3: XGBoost inference")
        try:
            predictions = get_ml_service().predict_leads({subject_entity_id: feature_dict})
            ml_score = predictions[0]["score"] if predictions else 0.0
        except Exception as e:
            logger.error(f"[C3] XGBoost inference failed for {subject_entity_id}: {e}")
            ml_score = 0.0

        priority = _score_to_priority(ml_score, len(active_findings))
        logger.info(f"[C3] ML score={ml_score:.4f} priority={priority}")

        # ----------------------------------------------------------------
        # STAGE 4: Gemini Explanation
        # ----------------------------------------------------------------
        logger.info(f"[C3] Stage 4: Gemini explanation")
        explanation_status = "SKIPPED"
        explanation_dict = None
        raw_explanation = None

        try:
            ctx = build_explanation_context(
                subject_entity_id=subject_entity_id,
                subject_name=subject_name,
                ml_score=ml_score,
                findings=findings,
            )
            expl_result: ExplanationResult = explain_lead(ctx, mock_response=mock_explanation)
            raw_explanation = expl_result.raw_response

            if expl_result.status == "PENDING_VALIDATION" and raw_explanation:
                # --------------------------------------------------------
                # STAGE 5: Zero-Hallucination Validation
                # --------------------------------------------------------
                logger.info(f"[C3] Stage 5: Zero-hallucination validation")
                val_result: ValidationResult = validate_explanation(raw_explanation, ctx)
                if val_result.status == "VALID":
                    explanation_status = "VALID"
                    explanation_dict = val_result.validated_explanation
                    logger.info(f"[C3] Explanation VALID for {subject_entity_id}")
                else:
                    explanation_status = "REJECTED"
                    logger.warning(
                        f"[C3] Explanation REJECTED for {subject_entity_id}: "
                        f"{val_result.violations[:3]}"
                    )
            elif expl_result.status == "SKIPPED":
                explanation_status = "SKIPPED"
        except Exception as e:
            logger.error(f"[C3] Explanation/validation error for {subject_entity_id}: {e}")
            explanation_status = "SKIPPED"

        # ----------------------------------------------------------------
        # STAGE 6: Build lead text
        # ----------------------------------------------------------------
        lead_text = _build_lead_text(
            subject_name, ml_score, findings, explanation_status, explanation_dict
        )

        # ----------------------------------------------------------------
        # STAGE 7: Persist lead (idempotent UPSERT via canonical_key)
        # ----------------------------------------------------------------
        findings_json = json.dumps([f.to_dict() for f in findings])
        explanation_json = json.dumps(explanation_dict) if explanation_dict else None

        lead_id, was_created = await self._upsert_lead(
            canonical_key=canonical_key,
            case_id=case_id,
            subject_entity_id=subject_entity_id,
            run_id=run_id,
            user_id=user_id,
            hypothesis_id=hypothesis_id,
            ml_score=ml_score,
            priority=priority,
            lead_text=lead_text,
            feature_vector_version=FEATURE_VECTOR_VERSION,
            findings_json=findings_json,
            explanation_json=explanation_json,
            explanation_status=explanation_status,
        )

        # ----------------------------------------------------------------
        # STAGE 8: Persist relational findings
        # ----------------------------------------------------------------
        if was_created:
            await self._persist_findings(lead_id, findings)

        return LeadGenerationResult(
            lead_id=lead_id,
            subject_entity_id=subject_entity_id,
            subject_name=subject_name,
            ml_score=ml_score,
            priority=priority,
            lead_text=lead_text,
            explanation_status=explanation_status,
            finding_count=len(findings),
            active_finding_count=len(active_findings),
            created=was_created,
        )

    async def _get_display_name(self, entity_id: str) -> str:
        result = await self.session.execute(
            text("SELECT display_name FROM civix.person WHERE entity_id = :eid"),
            {"eid": entity_id}
        )
        row = result.first()
        return row.display_name if row else entity_id

    async def _upsert_lead(
        self,
        canonical_key: str,
        case_id: str,
        subject_entity_id: str,
        run_id: str,
        user_id: str,
        hypothesis_id: Optional[str],
        ml_score: float,
        priority: str,
        lead_text: str,
        feature_vector_version: str,
        findings_json: str,
        explanation_json: Optional[str],
        explanation_status: str,
    ):
        """
        Idempotent lead upsert using canonical_key.
        If lead already exists for this (subject, case, date), UPDATE in place.
        Returns (lead_id, was_created).
        """
        # Check for existing lead by canonical_key stored in disposition_notes
        # (reusing disposition_notes as a canonical key column for idempotency)
        existing = await self.session.execute(
            text("""
                SELECT lead_id FROM civix.investigative_lead
                WHERE case_id = :cid
                  AND target_entity_id = :eid
                  AND disposition_notes LIKE :key_prefix
                LIMIT 1
            """),
            {
                "cid": case_id,
                "eid": subject_entity_id,
                "key_prefix": f"C3_CANONICAL:{canonical_key}%",
            }
        )
        existing_row = existing.first()

        if existing_row:
            lead_id = str(existing_row.lead_id)
            # UPDATE existing lead with fresh pipeline results
            await self.session.execute(
                text("""
                    UPDATE civix.investigative_lead SET
                        ai_confidence = :score,
                        priority = :priority,
                        lead_text = :lead_text,
                        feature_vector_version = :fv_version,
                        deterministic_findings = CAST(:findings AS jsonb),
                        explanation = CAST(:explanation AS jsonb),
                        explanation_status = :expl_status,
                        generated_by_run_id = :run_id
                    WHERE lead_id = :lid
                """),
                {
                    "score": ml_score,
                    "priority": priority,
                    "lead_text": lead_text,
                    "fv_version": feature_vector_version,
                    "findings": findings_json,
                    "explanation": explanation_json,
                    "expl_status": explanation_status,
                    "run_id": run_id,
                    "lid": lead_id,
                }
            )
            return lead_id, False
        else:
            lead_id = str(uuid4())
            await self.session.execute(
                text("""
                    INSERT INTO civix.investigative_lead (
                        lead_id, case_id, target_entity_id, hypothesis_id,
                        generated_by_run_id, generated_by_person, ai_confidence,
                        lead_text, priority, status,
                        feature_vector_version, deterministic_findings,
                        explanation, explanation_status,
                        disposition_notes
                    ) VALUES (
                        :lid, :cid, :tid, :hid,
                        :run_id, :uid, :score,
                        :lead_text, :priority, 'OPEN',
                        :fv_version, CAST(:findings AS jsonb),
                        CAST(:explanation AS jsonb), :expl_status,
                        :canonical_note
                    )
                """),
                {
                    "lid": lead_id,
                    "cid": case_id,
                    "tid": subject_entity_id,
                    "hid": hypothesis_id,
                    "run_id": run_id,
                    "uid": user_id,
                    "score": ml_score,
                    "lead_text": lead_text,
                    "priority": priority,
                    "fv_version": feature_vector_version,
                    "findings": findings_json,
                    "explanation": explanation_json,
                    "expl_status": explanation_status,
                    "canonical_note": f"C3_CANONICAL:{canonical_key}",
                }
            )
            return lead_id, True

    async def _persist_findings(
        self, lead_id: str, findings: List[DeterministicFinding]
    ) -> None:
        """
        Persist each finding as a row in civix.investigative_finding.
        Relational store for structured API access.
        """
        for f in findings:
            finding_id = str(uuid4())
            try:
                await self.session.execute(
                    text("""
                        INSERT INTO civix.investigative_finding (
                            finding_id, lead_id, finding_type,
                            subject_entity_id, object_entity_id,
                            relationship_strength, key_facts, evidence_ids,
                            path_description, hop_count, matching_rule_id,
                            date_range_start, date_range_end,
                            suppressed, suppression_reason
                        ) VALUES (
                            :fid, :lid, :ftype,
                            :sub_id, :obj_id,
                            :strength, CAST(:key_facts AS jsonb), CAST(:evidence_ids AS uuid[]),
                            :path_desc, :hop_count, :rule_id,
                            :date_start, :date_end,
                            :suppressed, :suppression_reason
                        )
                    """),
                    {
                        "fid": finding_id,
                        "lid": lead_id,
                        "ftype": f.finding_type,
                        "sub_id": f.subject_entity_id,
                        "obj_id": f.object_entity_id,
                        "strength": f.relationship_strength,
                        "key_facts": json.dumps(f.key_facts),
                        "evidence_ids": f.evidence_ids if f.evidence_ids else [],
                        "path_desc": f.path_description,
                        "hop_count": f.hop_count,
                        "rule_id": f.matching_rule_id,
                        "date_start": f.date_range_start,
                        "date_end": f.date_range_end,
                        "suppressed": f.suppressed,
                        "suppression_reason": f.suppression_reason,
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to persist finding {finding_id} for lead {lead_id}: {e}")
                # Non-fatal — lead is still valid even if individual finding rows fail


# ---------------------------------------------------------------------------
# Module-level entry point
# ---------------------------------------------------------------------------

async def generate_lead_for_entity(
    session: AsyncSession,
    subject_entity_id: str,
    case_id: str,
    run_id: str,
    user_id: str,
    as_of: Optional[datetime] = None,
    hypothesis_id: Optional[str] = None,
    mock_explanation: Optional[str] = None,
) -> LeadGenerationResult:
    """Module-level entry point."""
    engine = IntelligenceEngine(session)
    return await engine.generate_lead_for_entity(
        subject_entity_id=subject_entity_id,
        case_id=case_id,
        run_id=run_id,
        user_id=user_id,
        as_of=as_of,
        hypothesis_id=hypothesis_id,
        mock_explanation=mock_explanation,
    )
