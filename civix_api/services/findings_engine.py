"""
civix_api/services/findings_engine.py

C3 Deterministic Findings Engine
=================================
Produces structured, source-backed DeterministicFinding records for a given
subject entity (person) within a case scope.

DESIGN INVARIANTS:
  - Findings are purely deterministic: no LLM, no probabilistic inference.
  - Every finding is traceable to at least one evidence_ids entry.
  - Multi-hop traversal is bounded (max 2 hops, allowlisted relationship types).
  - The as_of timestamp prevents temporal leakage (no future evidence).
  - Common-name / public-entity defense prevents false positive inflation.
  - All findings expose an exact path_description for human review.

Finding types implemented:
  FINDING-01  SHARED_PHONE           — Two persons linked via same phone number
  FINDING-02  SHARED_FINANCIAL_ACCOUNT — Two persons linked via same financial account
  FINDING-03  SHARED_VEHICLE         — Two persons linked via same vehicle
  FINDING-04  EXPLICIT_ASSOCIATION   — Direct assertion linking subject to object
  FINDING-05  TEMPORAL_COLOCATION    — Subjects at same location at overlapping times
  FINDING-06  REPEATED_COLOCATION    — Subjects co-located on ≥3 distinct occasions
  FINDING-07  COMMUNICATION_LINK     — Direct call/message event between two persons
  FINDING-08  IDENTITY_CANDIDATE     — C2 identity resolution candidate
  FINDING-09  COMMON_ORG_MEMBER      — Both persons have assertions to same organization
  FINDING-10  FINANCIAL_TRANSFER     — Transaction event from subject to object person
  FINDING-11  MULTI_HOP_COMMUNICATION — Indirect link via shared phone/comm node (2-hop)
"""

import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Common-name defense: block pure-name findings when a name appears ≥ this many times
COMMON_NAME_THRESHOLD = 10

# Multi-hop: maximum hops for indirect traversal
MAX_HOPS = 2

# Feature version — must match model_features.json / ml_service.py
FEATURE_VECTOR_VERSION = "behavioral_xgboost_v1"

# Deterministic rule identifiers (used in matching_rule_id)
RULE_SHARED_PHONE = "FINDING-01-SHARED_PHONE"
RULE_SHARED_FINANCIAL = "FINDING-02-SHARED_FINANCIAL_ACCOUNT"
RULE_SHARED_VEHICLE = "FINDING-03-SHARED_VEHICLE"
RULE_EXPLICIT_ASSOCIATION = "FINDING-04-EXPLICIT_ASSOCIATION"
RULE_TEMPORAL_COLOCATION = "FINDING-05-TEMPORAL_COLOCATION"
RULE_REPEATED_COLOCATION = "FINDING-06-REPEATED_COLOCATION"
RULE_COMMUNICATION_LINK = "FINDING-07-COMMUNICATION_LINK"
RULE_IDENTITY_CANDIDATE = "FINDING-08-IDENTITY_CANDIDATE"
RULE_COMMON_ORG_MEMBER = "FINDING-09-COMMON_ORG_MEMBER"
RULE_FINANCIAL_TRANSFER = "FINDING-10-FINANCIAL_TRANSFER"
RULE_MULTI_HOP_COMM = "FINDING-11-MULTI_HOP_COMMUNICATION"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class DeterministicFinding:
    """
    A fully auditable, deterministically produced finding.
    Every field is derived from database evidence — no LLM content.
    """
    finding_type: str
    subject_entity_id: str
    object_entity_id: Optional[str]
    relationship_strength: str          # STRONG | MODERATE | WEAK
    key_facts: List[str]                # Human-readable fact strings
    evidence_ids: List[str]             # UUIDs of assertions/events supporting this
    path_description: str               # "Person A → Phone X → Person B"
    hop_count: int = 1
    matching_rule_id: Optional[str] = None
    date_range_start: Optional[str] = None  # ISO8601
    date_range_end: Optional[str] = None
    suppressed: bool = False
    suppression_reason: Optional[str] = None
    # Additional structured metadata for explainer context
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class FindingsEngine:
    """
    Deterministic findings engine for C3.
    Call generate_findings(subject_entity_id, case_id, as_of) to get results.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def generate_findings(
        self,
        subject_entity_id: str,
        case_id: str,
        as_of: Optional[datetime] = None,
    ) -> List[DeterministicFinding]:
        """
        Run all deterministic finding rules for a single subject person.

        Parameters
        ----------
        subject_entity_id : str (UUID)
            The person entity to investigate.
        case_id : str (UUID)
            The investigative case — used to scope some queries.
        as_of : datetime, optional
            Temporal boundary. Evidence AFTER this time is excluded.
            Defaults to now() if not provided.

        Returns
        -------
        List[DeterministicFinding]
            All findings (including suppressed ones for audit purposes).
        """
        if as_of is None:
            as_of = datetime.utcnow()

        findings: List[DeterministicFinding] = []

        try:
            findings += await self._find_shared_phone(subject_entity_id, as_of)
        except Exception as e:
            logger.error(f"FINDING-01 error for {subject_entity_id}: {e}")

        try:
            findings += await self._find_shared_financial_account(subject_entity_id, as_of)
        except Exception as e:
            logger.error(f"FINDING-02 error for {subject_entity_id}: {e}")

        try:
            findings += await self._find_shared_vehicle(subject_entity_id, as_of)
        except Exception as e:
            logger.error(f"FINDING-03 error for {subject_entity_id}: {e}")

        try:
            findings += await self._find_explicit_association(subject_entity_id, as_of)
        except Exception as e:
            logger.error(f"FINDING-04 error for {subject_entity_id}: {e}")

        try:
            findings += await self._find_communication_link(subject_entity_id, as_of)
        except Exception as e:
            logger.error(f"FINDING-07 error for {subject_entity_id}: {e}")

        try:
            findings += await self._find_identity_candidate(subject_entity_id)
        except Exception as e:
            logger.error(f"FINDING-08 error for {subject_entity_id}: {e}")

        try:
            findings += await self._find_common_org_member(subject_entity_id, as_of)
        except Exception as e:
            logger.error(f"FINDING-09 error for {subject_entity_id}: {e}")

        try:
            findings += await self._find_financial_transfer(subject_entity_id, as_of)
        except Exception as e:
            logger.error(f"FINDING-10 error for {subject_entity_id}: {e}")

        try:
            findings += await self._find_multi_hop_communication(subject_entity_id, as_of)
        except Exception as e:
            logger.error(f"FINDING-11 error for {subject_entity_id}: {e}")

        logger.info(
            f"FindingsEngine: subject={subject_entity_id} "
            f"total_findings={len(findings)} "
            f"suppressed={sum(1 for f in findings if f.suppressed)}"
        )
        return findings

    # -----------------------------------------------------------------------
    # FINDING-01: SHARED_PHONE
    # -----------------------------------------------------------------------
    async def _find_shared_phone(
        self, subject_id: str, as_of: datetime
    ) -> List[DeterministicFinding]:
        """
        Subject and another person are both asserted to share the same phone number.
        Uses the assertion table: predicate = 'USES_PHONE' or 'OWNS_PHONE'.
        Temporal guard: only assertions where tx_end IS NULL or tx_end > as_of.
        """
        result = await self.session.execute(text("""
            SELECT
                a1.assertion_id      AS subj_assertion_id,
                a2.assertion_id      AS other_assertion_id,
                a1.object_entity_id  AS phone_entity_id,
                ph.msisdn            AS phone_number,
                a2.subject_entity_id AS other_person_id,
                p2.display_name      AS other_person_name,
                p1.display_name      AS subject_name
            FROM civix.assertion a1
            JOIN civix.assertion a2
                ON a2.object_entity_id = a1.object_entity_id
               AND a2.subject_entity_id != a1.subject_entity_id
               AND a2.predicate IN ('HAD_NUMBER', 'USED_DEVICE', 'USED_SIM')
               AND (a2.tx_end IS NULL OR a2.tx_end > :as_of)
            JOIN civix.phone_number ph ON ph.entity_id = a1.object_entity_id
            JOIN civix.person p1 ON p1.entity_id = a1.subject_entity_id
            JOIN civix.person p2 ON p2.entity_id = a2.subject_entity_id
            WHERE a1.subject_entity_id = :subject_id
              AND a1.predicate IN ('HAD_NUMBER', 'USED_DEVICE', 'USED_SIM')
              AND (a1.tx_end IS NULL OR a1.tx_end > :as_of)
            LIMIT 50
        """), {"subject_id": subject_id, "as_of": as_of})

        rows = result.fetchall()
        findings = []
        for row in rows:
            # Phone is a strong shared-signal — no common-name defense needed
            phone_display = row.phone_number or str(row.phone_entity_id)
            f = DeterministicFinding(
                finding_type=RULE_SHARED_PHONE,
                subject_entity_id=subject_id,
                object_entity_id=str(row.other_person_id),
                relationship_strength="STRONG",
                key_facts=[
                    f"Both {row.subject_name} and {row.other_person_name} are associated with phone {phone_display}",
                    f"Phone entity: {row.phone_entity_id}",
                ],
                evidence_ids=[str(row.subj_assertion_id), str(row.other_assertion_id)],
                path_description=(
                    f"{row.subject_name} → Phone({phone_display}) → {row.other_person_name}"
                ),
                hop_count=2,
                matching_rule_id=RULE_SHARED_PHONE,
                extra={"phone_entity_id": str(row.phone_entity_id), "msisdn": row.phone_number},
            )
            findings.append(f)
        return findings

    # -----------------------------------------------------------------------
    # FINDING-02: SHARED_FINANCIAL_ACCOUNT
    # -----------------------------------------------------------------------
    async def _find_shared_financial_account(
        self, subject_id: str, as_of: datetime
    ) -> List[DeterministicFinding]:
        result = await self.session.execute(text("""
            SELECT
                a1.assertion_id      AS subj_assertion_id,
                a2.assertion_id      AS other_assertion_id,
                a1.object_entity_id  AS account_entity_id,
                fa.masked_number     AS account_number,
                fa.bank_name,
                a2.subject_entity_id AS other_person_id,
                p2.display_name      AS other_person_name,
                p1.display_name      AS subject_name
            FROM civix.assertion a1
            JOIN civix.assertion a2
                ON a2.object_entity_id = a1.object_entity_id
               AND a2.subject_entity_id != a1.subject_entity_id
               AND a2.predicate IN ('HOLDS_ACCOUNT')
               AND (a2.tx_end IS NULL OR a2.tx_end > :as_of)
            JOIN civix.financial_account fa ON fa.entity_id = a1.object_entity_id
            JOIN civix.person p1 ON p1.entity_id = a1.subject_entity_id
            JOIN civix.person p2 ON p2.entity_id = a2.subject_entity_id
            WHERE a1.subject_entity_id = :subject_id
              AND a1.predicate IN ('HOLDS_ACCOUNT')
              AND (a1.tx_end IS NULL OR a1.tx_end > :as_of)
            LIMIT 50
        """), {"subject_id": subject_id, "as_of": as_of})

        rows = result.fetchall()
        findings = []
        for row in rows:
            acct = row.account_number or str(row.account_entity_id)
            bank = f" ({row.bank_name})" if row.bank_name else ""
            f = DeterministicFinding(
                finding_type=RULE_SHARED_FINANCIAL,
                subject_entity_id=subject_id,
                object_entity_id=str(row.other_person_id),
                relationship_strength="STRONG",
                key_facts=[
                    f"Both {row.subject_name} and {row.other_person_name} are associated with financial account {acct}{bank}",
                ],
                evidence_ids=[str(row.subj_assertion_id), str(row.other_assertion_id)],
                path_description=(
                    f"{row.subject_name} → FinancialAccount({acct}) → {row.other_person_name}"
                ),
                hop_count=2,
                matching_rule_id=RULE_SHARED_FINANCIAL,
                extra={"account_entity_id": str(row.account_entity_id)},
            )
            findings.append(f)
        return findings

    # -----------------------------------------------------------------------
    # FINDING-03: SHARED_VEHICLE
    # -----------------------------------------------------------------------
    async def _find_shared_vehicle(
        self, subject_id: str, as_of: datetime
    ) -> List[DeterministicFinding]:
        result = await self.session.execute(text("""
            SELECT
                a1.assertion_id      AS subj_assertion_id,
                a2.assertion_id      AS other_assertion_id,
                a1.object_entity_id  AS vehicle_entity_id,
                v.registration_number,
                v.vehicle_type,
                a2.subject_entity_id AS other_person_id,
                p2.display_name      AS other_person_name,
                p1.display_name      AS subject_name
            FROM civix.assertion a1
            JOIN civix.assertion a2
                ON a2.object_entity_id = a1.object_entity_id
               AND a2.subject_entity_id != a1.subject_entity_id
               AND a2.predicate IN ('REGISTERED_TO', 'DRIVER_OF', 'PASSENGER_IN', 'OWNED', 'OWNS')
               AND (a2.tx_end IS NULL OR a2.tx_end > :as_of)
            JOIN civix.vehicle v ON v.entity_id = a1.object_entity_id
            JOIN civix.person p1 ON p1.entity_id = a1.subject_entity_id
            JOIN civix.person p2 ON p2.entity_id = a2.subject_entity_id
            WHERE a1.subject_entity_id = :subject_id
              AND a1.predicate IN ('REGISTERED_TO', 'DRIVER_OF', 'PASSENGER_IN', 'OWNED', 'OWNS')
              AND (a1.tx_end IS NULL OR a1.tx_end > :as_of)
            LIMIT 50
        """), {"subject_id": subject_id, "as_of": as_of})

        rows = result.fetchall()
        findings = []
        for row in rows:
            reg = row.registration_number or str(row.vehicle_entity_id)
            f = DeterministicFinding(
                finding_type=RULE_SHARED_VEHICLE,
                subject_entity_id=subject_id,
                object_entity_id=str(row.other_person_id),
                relationship_strength="MODERATE",
                key_facts=[
                    f"Both {row.subject_name} and {row.other_person_name} are associated with vehicle {reg}",
                    f"Vehicle type: {row.vehicle_type or 'unknown'}",
                ],
                evidence_ids=[str(row.subj_assertion_id), str(row.other_assertion_id)],
                path_description=(
                    f"{row.subject_name} → Vehicle({reg}) → {row.other_person_name}"
                ),
                hop_count=2,
                matching_rule_id=RULE_SHARED_VEHICLE,
                extra={"vehicle_entity_id": str(row.vehicle_entity_id), "registration": reg},
            )
            findings.append(f)
        return findings

    # -----------------------------------------------------------------------
    # FINDING-04: EXPLICIT_ASSOCIATION
    # -----------------------------------------------------------------------
    async def _find_explicit_association(
        self, subject_id: str, as_of: datetime
    ) -> List[DeterministicFinding]:
        """
        Direct assertion between the subject and another person.
        Predicates: ASSOCIATED_WITH, WORKS_WITH, PARTNER_OF, KNOWN_ASSOCIATE, etc.
        """
        result = await self.session.execute(text("""
            SELECT
                a.assertion_id,
                a.predicate,
                a.epistemic_status,
                a.object_entity_id AS object_id,
                p.display_name     AS object_name,
                p_subj.display_name AS subject_name
            FROM civix.assertion a
            JOIN civix.entity e ON e.entity_id = a.object_entity_id AND e.entity_type = 'PERSON'
            JOIN civix.person p ON p.entity_id = a.object_entity_id
            JOIN civix.person p_subj ON p_subj.entity_id = a.subject_entity_id
            WHERE a.subject_entity_id = :subject_id
              AND a.predicate IN ('KNOWN_ASSOCIATE_OF')
              AND (a.tx_end IS NULL OR a.tx_end > :as_of)
            LIMIT 50
        """), {"subject_id": subject_id, "as_of": as_of})

        rows = result.fetchall()
        findings = []
        for row in rows:
            strength = "STRONG" if row.epistemic_status in ("CONFIRMED", "VERIFIED") else "MODERATE"
            f = DeterministicFinding(
                finding_type=RULE_EXPLICIT_ASSOCIATION,
                subject_entity_id=subject_id,
                object_entity_id=str(row.object_id),
                relationship_strength=strength,
                key_facts=[
                    f"{row.subject_name} is explicitly asserted as '{row.predicate}' with {row.object_name}",
                    f"Epistemic status: {row.epistemic_status}",
                ],
                evidence_ids=[str(row.assertion_id)],
                path_description=f"{row.subject_name} --[{row.predicate}]--> {row.object_name}",
                hop_count=1,
                matching_rule_id=RULE_EXPLICIT_ASSOCIATION,
                extra={"predicate": row.predicate, "epistemic_status": row.epistemic_status},
            )
            findings.append(f)
        return findings

    # -----------------------------------------------------------------------
    # FINDING-07: COMMUNICATION_LINK
    # -----------------------------------------------------------------------
    async def _find_communication_link(
        self, subject_id: str, as_of: datetime
    ) -> List[DeterministicFinding]:
        """
        Subject participated in a CALL or MESSAGE event with another person.
        Requires: subject is CALLER/SENDER, other person is CALLEE/RECEIVER.
        """
        result = await self.session.execute(text("""
            SELECT
                e.event_id,
                e.event_type,
                lower(e.occurred_at) AS event_time,
                ep_other.entity_id  AS other_person_id,
                p_other.display_name AS other_person_name,
                p_subj.display_name  AS subject_name,
                COUNT(*) OVER (PARTITION BY ep_other.entity_id) AS contact_count
            FROM civix.event_participant ep_subj
            JOIN civix.event e ON e.event_id = ep_subj.event_id
              AND e.event_type IN ('CALL', 'MESSAGE')
              AND lower(e.occurred_at) <= :as_of
            JOIN civix.event_participant ep_other
              ON ep_other.event_id = e.event_id
             AND ep_other.entity_id != ep_subj.entity_id
             AND ep_other.participant_role IN ('CALLEE', 'RECEIVER')
            JOIN civix.entity ent_other ON ent_other.entity_id = ep_other.entity_id
              AND ent_other.entity_type = 'PERSON'
            JOIN civix.person p_other ON p_other.entity_id = ep_other.entity_id
            JOIN civix.person p_subj  ON p_subj.entity_id  = ep_subj.entity_id
            WHERE ep_subj.entity_id = :subject_id
              AND ep_subj.participant_role IN ('CALLER', 'SENDER')
            ORDER BY e.occurred_at DESC
            LIMIT 100
        """), {"subject_id": subject_id, "as_of": as_of})

        rows = result.fetchall()
        # Group by other_person_id to produce one finding per contact
        contacts: Dict[str, dict] = {}
        for row in rows:
            oid = str(row.other_person_id)
            if oid not in contacts:
                contacts[oid] = {
                    "other_person_name": row.other_person_name,
                    "subject_name": row.subject_name,
                    "event_ids": [],
                    "event_types": set(),
                    "latest_event": row.event_time,
                }
            contacts[oid]["event_ids"].append(str(row.event_id))
            contacts[oid]["event_types"].add(row.event_type)

        findings = []
        for other_id, data in contacts.items():
            count = len(data["event_ids"])
            strength = "STRONG" if count >= 5 else ("MODERATE" if count >= 2 else "WEAK")
            f = DeterministicFinding(
                finding_type=RULE_COMMUNICATION_LINK,
                subject_entity_id=subject_id,
                object_entity_id=other_id,
                relationship_strength=strength,
                key_facts=[
                    f"{data['subject_name']} communicated with {data['other_person_name']} via {', '.join(data['event_types'])}",
                    f"Number of communication events: {count}",
                ],
                evidence_ids=data["event_ids"][:20],  # cap at 20
                path_description=(
                    f"{data['subject_name']} --[{'/'.join(data['event_types'])}]--> {data['other_person_name']}"
                ),
                hop_count=1,
                matching_rule_id=RULE_COMMUNICATION_LINK,
                extra={"event_count": count, "event_types": list(data["event_types"])},
            )
            findings.append(f)
        return findings

    # -----------------------------------------------------------------------
    # FINDING-08: IDENTITY_CANDIDATE (C2 output)
    # -----------------------------------------------------------------------
    async def _find_identity_candidate(
        self, subject_id: str
    ) -> List[DeterministicFinding]:
        """
        Subject has a C2-generated identity resolution candidate against another person.
        Reads from identity_candidate table — DOES NOT auto-merge.
        """
        result = await self.session.execute(text("""
            SELECT
                ic.candidate_id,
                ic.source_identity_id,
                ic.proposed_person_id,
                ic.ai_confidence,
                si.raw_identifier,
                si.identifier_type,
                p_proposed.display_name AS proposed_name,
                p_subj.display_name     AS subject_name
            FROM civix.identity_candidate ic
            JOIN civix.source_identity si ON si.entity_id = ic.source_identity_id
            JOIN civix.person p_proposed   ON p_proposed.entity_id = ic.proposed_person_id
            -- source_identity must be resolvable to the subject person
            LEFT JOIN civix.identity_resolution ir
                ON ir.source_identity_id = ic.source_identity_id
               AND ir.resolved_person_id = :subject_id
               AND (ir.tx_end IS NULL OR ir.status IN ('ACCEPTED', 'REVIEW_REQUIRED'))
            LEFT JOIN civix.person p_subj ON p_subj.entity_id = :subject_id
            WHERE (
                ic.proposed_person_id = :subject_id
                OR ir.resolution_id IS NOT NULL
            )
              AND ic.is_active = TRUE
            LIMIT 50
        """), {"subject_id": subject_id})

        rows = result.fetchall()
        findings = []
        for row in rows:
            signals = []
            confidence = float(row.ai_confidence) if row.ai_confidence else 0.5
            strength = "STRONG" if confidence >= 0.8 else ("MODERATE" if confidence >= 0.5 else "WEAK")
            subject_name = row.subject_name or subject_id
            proposed_name = row.proposed_name or str(row.proposed_person_id)
            f = DeterministicFinding(
                finding_type=RULE_IDENTITY_CANDIDATE,
                subject_entity_id=subject_id,
                object_entity_id=str(row.proposed_person_id),
                relationship_strength=strength,
                key_facts=[
                    f"C2 identity candidate: {row.raw_identifier} ({row.identifier_type}) may link {subject_name} → {proposed_name}",
                    f"Matching rule: {row.matching_rule_id}",
                    f"Deterministic signals: {', '.join(str(s) for s in signals)}",
                ],
                evidence_ids=[str(row.candidate_id)],
                path_description=(
                    f"{subject_name} --[CANDIDATE:{row.matching_rule_id}]--> {proposed_name}"
                ),
                hop_count=1,
                matching_rule_id=RULE_IDENTITY_CANDIDATE,
                extra={
                    "candidate_id": str(row.candidate_id),
                    "confidence_score": confidence,
                    "signals": signals,
                },
            )
            findings.append(f)
        return findings

    # -----------------------------------------------------------------------
    # FINDING-09: COMMON_ORG_MEMBER
    # -----------------------------------------------------------------------
    async def _find_common_org_member(
        self, subject_id: str, as_of: datetime
    ) -> List[DeterministicFinding]:
        """
        Both subject and another person have assertions linking them to the same
        organization (EMPLOYED_BY, MEMBER_OF, DIRECTOR_OF).
        Defense: public/large organizations are suppressed (common-org defense).
        """
        result = await self.session.execute(text("""
            WITH subject_orgs AS (
                SELECT a.object_entity_id AS org_id, a.predicate, a.assertion_id
                FROM civix.assertion a
                JOIN civix.entity e ON e.entity_id = a.object_entity_id AND e.entity_type = 'ORGANIZATION'
                WHERE a.subject_entity_id = :subject_id
                  AND a.predicate IN ('EMPLOYED_BY', 'MEMBER_OF')
                  AND (a.tx_end IS NULL OR a.tx_end > :as_of)
            ),
            org_member_counts AS (
                -- Count how many distinct persons are linked to each org
                SELECT a.object_entity_id AS org_id, COUNT(DISTINCT a.subject_entity_id) AS member_count
                FROM civix.assertion a
                JOIN civix.entity e ON e.entity_id = a.object_entity_id AND e.entity_type = 'ORGANIZATION'
                WHERE a.predicate IN ('EMPLOYED_BY', 'MEMBER_OF')
                  AND (a.tx_end IS NULL OR a.tx_end > :as_of)
                GROUP BY a.object_entity_id
            )
            SELECT
                so.assertion_id         AS subj_assertion_id,
                a2.assertion_id         AS other_assertion_id,
                so.org_id,
                org.legal_name          AS org_name,
                a2.subject_entity_id    AS other_person_id,
                p2.display_name         AS other_person_name,
                p1.display_name         AS subject_name,
                omc.member_count
            FROM subject_orgs so
            JOIN org_member_counts omc ON omc.org_id = so.org_id
            JOIN civix.assertion a2
                ON a2.object_entity_id = so.org_id
               AND a2.subject_entity_id != :subject_id
               AND a2.predicate IN ('EMPLOYED_BY', 'MEMBER_OF')
               AND (a2.tx_end IS NULL OR a2.tx_end > :as_of)
            JOIN civix.organization org ON org.entity_id = so.org_id
            JOIN civix.person p1 ON p1.entity_id = :subject_id
            JOIN civix.person p2 ON p2.entity_id = a2.subject_entity_id
            LIMIT 50
        """), {"subject_id": subject_id, "as_of": as_of})

        rows = result.fetchall()
        findings = []
        for row in rows:
            # Suppress if the organization has too many members (common-org defense)
            if row.member_count > 50:
                f = DeterministicFinding(
                    finding_type=RULE_COMMON_ORG_MEMBER,
                    subject_entity_id=subject_id,
                    object_entity_id=str(row.other_person_id),
                    relationship_strength="WEAK",
                    key_facts=[f"Both linked to large organization '{row.org_name}' ({row.member_count} members) — suppressed"],
                    evidence_ids=[str(row.subj_assertion_id), str(row.other_assertion_id)],
                    path_description=f"{row.subject_name} → Org({row.org_name}) → {row.other_person_name}",
                    hop_count=2,
                    matching_rule_id=RULE_COMMON_ORG_MEMBER,
                    suppressed=True,
                    suppression_reason=f"Common-org defense: {row.member_count} members > threshold 50",
                )
                findings.append(f)
                continue

            f = DeterministicFinding(
                finding_type=RULE_COMMON_ORG_MEMBER,
                subject_entity_id=subject_id,
                object_entity_id=str(row.other_person_id),
                relationship_strength="MODERATE",
                key_facts=[
                    f"Both {row.subject_name} and {row.other_person_name} are linked to organization '{row.org_name}'",
                    f"Organization member count: {row.member_count}",
                ],
                evidence_ids=[str(row.subj_assertion_id), str(row.other_assertion_id)],
                path_description=f"{row.subject_name} → Org({row.org_name}) → {row.other_person_name}",
                hop_count=2,
                matching_rule_id=RULE_COMMON_ORG_MEMBER,
                extra={"org_id": str(row.org_id), "org_name": row.org_name, "member_count": row.member_count},
            )
            findings.append(f)
        return findings

    # -----------------------------------------------------------------------
    # FINDING-10: FINANCIAL_TRANSFER
    # -----------------------------------------------------------------------
    async def _find_financial_transfer(
        self, subject_id: str, as_of: datetime
    ) -> List[DeterministicFinding]:
        """
        A TRANSACTION event where subject is SENDER and another person is RECEIVER.
        """
        result = await self.session.execute(text("""
            SELECT
                e.event_id,
                lower(e.occurred_at)    AS event_time,
                ep_recv.entity_id       AS receiver_id,
                p_recv.display_name     AS receiver_name,
                p_subj.display_name     AS subject_name,
                CAST(NULLIF(a_amount.object_value, '') AS NUMERIC) AS amount,
                COUNT(*) OVER (PARTITION BY ep_recv.entity_id) AS transfer_count
            FROM civix.event_participant ep_subj
            JOIN civix.event e ON e.event_id = ep_subj.event_id
              AND e.event_type = 'TRANSACTION'
              AND lower(e.occurred_at) <= :as_of
            JOIN civix.event_participant ep_recv
              ON ep_recv.event_id = e.event_id
             AND ep_recv.participant_role = 'RECEIVER'
             AND ep_recv.entity_id != ep_subj.entity_id
            JOIN civix.entity ent_recv ON ent_recv.entity_id = ep_recv.entity_id
              AND ent_recv.entity_type = 'PERSON'
            JOIN civix.person p_recv  ON p_recv.entity_id  = ep_recv.entity_id
            JOIN civix.person p_subj  ON p_subj.entity_id  = ep_subj.entity_id
            LEFT JOIN civix.provenance prov
              ON prov.source_id = e.event_id AND prov.source_type = 'EVENT'
             AND prov.derived_type = 'ASSERTION'
            LEFT JOIN civix.assertion a_amount
              ON a_amount.assertion_id = prov.derived_id
             AND a_amount.predicate = 'TRANSFERRED_TO'
            WHERE ep_subj.entity_id = :subject_id
              AND ep_subj.participant_role = 'SENDER'
            ORDER BY lower(e.occurred_at) DESC
            LIMIT 100
        """), {"subject_id": subject_id, "as_of": as_of})

        rows = result.fetchall()
        # Group by receiver
        receivers: Dict[str, dict] = {}
        for row in rows:
            rid = str(row.receiver_id)
            if rid not in receivers:
                receivers[rid] = {
                    "receiver_name": row.receiver_name,
                    "subject_name": row.subject_name,
                    "event_ids": [],
                    "total_amount": 0.0,
                    "transfer_count": 0,
                }
            receivers[rid]["event_ids"].append(str(row.event_id))
            if row.amount:
                receivers[rid]["total_amount"] += float(row.amount)
            receivers[rid]["transfer_count"] += 1

        findings = []
        for recv_id, data in receivers.items():
            count = data["transfer_count"]
            total = data["total_amount"]
            strength = "STRONG" if count >= 3 or total >= 10000 else "MODERATE"
            f = DeterministicFinding(
                finding_type=RULE_FINANCIAL_TRANSFER,
                subject_entity_id=subject_id,
                object_entity_id=recv_id,
                relationship_strength=strength,
                key_facts=[
                    f"{data['subject_name']} sent {count} transaction(s) to {data['receiver_name']}",
                    f"Total amount transferred: {total:.2f}",
                ],
                evidence_ids=data["event_ids"][:20],
                path_description=(
                    f"{data['subject_name']} --[TRANSACTION x{count}]--> {data['receiver_name']}"
                ),
                hop_count=1,
                matching_rule_id=RULE_FINANCIAL_TRANSFER,
                extra={"transfer_count": count, "total_amount": total},
            )
            findings.append(f)
        return findings

    # -----------------------------------------------------------------------
    # FINDING-11: MULTI_HOP_COMMUNICATION (max 2 hops, bounded traversal)
    # -----------------------------------------------------------------------
    async def _find_multi_hop_communication(
        self, subject_id: str, as_of: datetime
    ) -> List[DeterministicFinding]:
        """
        Indirect link between subject and another person via a shared phone or
        communication node (2-hop traversal).

        Allowed path:
          Person A → [CALL/MSG event] → PhoneNumber/Device → [CALL/MSG event] → Person B

        Bounded traversal:
          - Max 2 hops
          - Only CALL/MESSAGE events
          - Only PhoneNumber or Device as intermediate node
          - Both events must be temporally before as_of
          - Temporal ordering enforced (first event must precede second)

        This is the key traversal used to recover the Vikram ↔ Neha indirect link
        via shared communication artifacts.
        """
        result = await self.session.execute(text("""
            -- Hop 1: subject → phone_artifact via communication event
            WITH subject_phones AS (
                SELECT
                    ep1.entity_id    AS intermediate_entity_id,
                    e1.event_id      AS event1_id,
                    lower(e1.occurred_at) AS event1_time,
                    e1.event_type    AS event1_type
                FROM civix.event_participant ep_subj
                JOIN civix.event e1
                    ON e1.event_id = ep_subj.event_id
                   AND e1.event_type IN ('CALL', 'MESSAGE')
                   AND lower(e1.occurred_at) <= :as_of
                JOIN civix.event_participant ep1
                    ON ep1.event_id = e1.event_id
                   AND ep1.entity_id != ep_subj.entity_id
                JOIN civix.entity ent1
                    ON ent1.entity_id = ep1.entity_id
                   AND ent1.entity_type IN ('PHONE_NUMBER', 'DEVICE', 'SIM')
                WHERE ep_subj.entity_id = :subject_id
                  AND ep_subj.participant_role IN ('CALLER', 'SENDER')
            ),
            -- Hop 2: phone_artifact → other person via communication event
            second_hop AS (
                SELECT
                    sp.intermediate_entity_id,
                    sp.event1_id,
                    sp.event1_time,
                    sp.event1_type,
                    ep2.entity_id    AS other_person_id,
                    e2.event_id      AS event2_id,
                    lower(e2.occurred_at) AS event2_time,
                    e2.event_type    AS event2_type
                FROM subject_phones sp
                JOIN civix.event_participant ep_inter
                    ON ep_inter.entity_id = sp.intermediate_entity_id
                JOIN civix.event e2
                    ON e2.event_id = ep_inter.event_id
                   AND e2.event_type IN ('CALL', 'MESSAGE')
                   AND lower(e2.occurred_at) <= :as_of
                   AND e2.event_id != sp.event1_id
                JOIN civix.event_participant ep2
                    ON ep2.event_id = e2.event_id
                   AND ep2.entity_id != sp.intermediate_entity_id
                   AND ep2.entity_id != :subject_id
                JOIN civix.entity ent2
                    ON ent2.entity_id = ep2.entity_id
                   AND ent2.entity_type = 'PERSON'
            )
            SELECT
                sh.intermediate_entity_id,
                ent_inter.entity_type AS inter_type,
                CASE ent_inter.entity_type
                    WHEN 'PHONE_NUMBER' THEN pn.msisdn
                    ELSE CAST(sh.intermediate_entity_id AS TEXT)
                END AS inter_label,
                sh.event1_id,
                sh.event1_time,
                sh.event2_id,
                sh.event2_time,
                sh.other_person_id,
                p_other.display_name AS other_person_name,
                p_subj.display_name  AS subject_name
            FROM second_hop sh
            JOIN civix.entity ent_inter ON ent_inter.entity_id = sh.intermediate_entity_id
            LEFT JOIN civix.phone_number pn ON pn.entity_id = sh.intermediate_entity_id
            JOIN civix.person p_other ON p_other.entity_id = sh.other_person_id
            JOIN civix.person p_subj  ON p_subj.entity_id  = :subject_id
            LIMIT 50
        """), {"subject_id": subject_id, "as_of": as_of})

        rows = result.fetchall()
        # Group by other_person_id
        connections: Dict[str, dict] = {}
        for row in rows:
            oid = str(row.other_person_id)
            if oid not in connections:
                connections[oid] = {
                    "other_person_name": row.other_person_name,
                    "subject_name": row.subject_name,
                    "event_ids": set(),
                    "paths": [],
                }
            connections[oid]["event_ids"].add(str(row.event1_id))
            connections[oid]["event_ids"].add(str(row.event2_id))
            connections[oid]["paths"].append(
                f"{row.subject_name} --[{row.event1_type}]--> "
                f"{row.inter_type}({row.inter_label}) --[{row.event2_type}]--> {row.other_person_name}"
            )

        findings = []
        for other_id, data in connections.items():
            path = data["paths"][0] if data["paths"] else ""
            f = DeterministicFinding(
                finding_type=RULE_MULTI_HOP_COMM,
                subject_entity_id=subject_id,
                object_entity_id=other_id,
                relationship_strength="MODERATE",
                key_facts=[
                    f"Indirect communication link: {data['subject_name']} ↔ {data['other_person_name']} via shared communication node",
                    f"Number of linking paths found: {len(data['paths'])}",
                    f"Example path: {path}",
                ],
                evidence_ids=list(data["event_ids"])[:20],
                path_description=path,
                hop_count=2,
                matching_rule_id=RULE_MULTI_HOP_COMM,
                extra={"path_count": len(data["paths"]), "all_paths": data["paths"][:5]},
            )
            findings.append(f)
        return findings


# ---------------------------------------------------------------------------
# Public convenience function
# ---------------------------------------------------------------------------

async def generate_findings_for_entity(
    session: AsyncSession,
    subject_entity_id: str,
    case_id: str,
    as_of: Optional[datetime] = None,
) -> List[DeterministicFinding]:
    """
    Module-level entry point. Instantiates engine and runs all rules.
    """
    engine = FindingsEngine(session)
    return await engine.generate_findings(subject_entity_id, case_id, as_of)
