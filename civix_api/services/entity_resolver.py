import logging
from uuid import UUID
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Dict

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)
class EntityResolver:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def run(self, analysis_run_id: UUID) -> Dict[str, int]:
        """
        Executes all deterministic candidate generation rules.
        Uses blocking to efficiently match identities.
        Returns statistics of generated candidates.
        """
        stats = {
            "RULE_01_NAME_PHONE": 0,
            "RULE_02_NAME_ACCOUNT": 0,
            "RULE_03_ALIAS_VEHICLE": 0,
            "RULE_04_NAME_ORG": 0,
            "total_candidates": 0
        }
        
        # We will use temporary tables to normalize names for efficient joining
        await self._setup_temp_tables()
        
        # Run blocking rules
        stats["RULE_01_NAME_PHONE"] = await self._run_rule_name_phone(analysis_run_id)
        stats["RULE_02_NAME_ACCOUNT"] = await self._run_rule_name_account(analysis_run_id)
        stats["RULE_03_ALIAS_VEHICLE"] = await self._run_rule_alias_vehicle(analysis_run_id)
        stats["RULE_04_NAME_ORG"] = await self._run_rule_name_org(analysis_run_id)
        
        # Sum stats
        stats["total_candidates"] = sum(v for k, v in stats.items() if k != "total_candidates")
        return stats

    async def _setup_temp_tables(self):
        # Create temp table with normalized names for Person
        await self.session.execute(text("""
            CREATE TEMP TABLE IF NOT EXISTS temp_person_norm ON COMMIT DROP AS
            SELECT 
                entity_id AS person_id,
                upper(regexp_replace(display_name, '[^a-zA-Z0-9]', '', 'g')) AS norm_name
            FROM civix.person
        """))
        await self.session.execute(text("CREATE INDEX IF NOT EXISTS idx_temp_person_norm ON temp_person_norm(norm_name)"))
        
        # Create temp table with normalized names for SourceIdentity (type = NAME)
        await self.session.execute(text("""
            CREATE TEMP TABLE IF NOT EXISTS temp_source_norm ON COMMIT DROP AS
            SELECT 
                entity_id AS source_identity_id,
                upper(regexp_replace(raw_identifier, '[^a-zA-Z0-9]', '', 'g')) AS norm_name
            FROM civix.source_identity
            WHERE identifier_type = 'NAME'
        """))
        await self.session.execute(text("CREATE INDEX IF NOT EXISTS idx_temp_source_norm ON temp_source_norm(norm_name)"))

    async def _get_common_names(self, threshold: int = 10) -> set:
        res = await self.session.execute(text("""
            SELECT norm_name 
            FROM (
                SELECT norm_name FROM temp_person_norm
                UNION ALL
                SELECT norm_name FROM temp_source_norm
            ) all_names
            WHERE norm_name IS NOT NULL AND norm_name != ''
            GROUP BY norm_name
            HAVING COUNT(*) > :thresh
        """), {"thresh": threshold})
        return {row.norm_name for row in res}

    async def _upsert_candidates(self, candidates: List[Dict]):
        if not candidates:
            return 0
            
        count = 0
        for c in candidates:
            # Check if candidate exists and its resolution status
            res = await self.session.execute(text("""
                SELECT c.candidate_id, c.supporting_evidence_ids, r.status
                FROM civix.identity_candidate c
                LEFT JOIN civix.identity_resolution r ON r.candidate_id = c.candidate_id
                WHERE c.source_identity_id = :si_id AND c.proposed_person_id = :p_id
                ORDER BY r.tx_start DESC NULLS LAST LIMIT 1
            """), {"si_id": c["source_identity_id"], "p_id": c["proposed_person_id"]})
            
            existing = res.fetchone()
            if existing:
                existing_ev = set(existing.supporting_evidence_ids)
                new_ev = set(c["evidence_ids"])
                
                # If REJECTED, only regenerate if there is materially NEW evidence
                if existing.status == 'REJECTED' and new_ev.issubset(existing_ev):
                    continue  # Unchanged evidence, do not regenerate

            # Upsert
            res = await self.session.execute(text("""
                INSERT INTO civix.identity_candidate (
                    source_identity_id, 
                    proposed_person_id, 
                    ai_confidence, 
                    analysis_run_id,
                    matching_rule_id,
                    deterministic_signals,
                    supporting_evidence_ids,
                    is_active
                )
                VALUES (
                    :si_id, :p_id, 1.0, :run_id, :rule_id, CAST(:signals AS jsonb), :ev_ids, TRUE
                )
                ON CONFLICT (source_identity_id, proposed_person_id) 
                DO UPDATE SET 
                    is_active = TRUE,
                    analysis_run_id = EXCLUDED.analysis_run_id,
                    matching_rule_id = EXCLUDED.matching_rule_id,
                    deterministic_signals = CAST(:signals AS jsonb),
                    supporting_evidence_ids = EXCLUDED.supporting_evidence_ids
                RETURNING candidate_id
            """), {
                "si_id": c["source_identity_id"],
                "p_id": c["proposed_person_id"],
                "run_id": c["analysis_run_id"],
                "rule_id": c["rule_id"],
                "signals": json.dumps(c["signals"]),
                "ev_ids": list(set(c["evidence_ids"]))
            })
            if res.fetchone():
                count += 1
        return count

    async def _run_rule_name_phone(self, analysis_run_id: UUID) -> int:
        """
        RULE_01: Exact Normalized Name + Shared Phone Number
        """
        # A person and a source_identity both OWN the same phone_number
        query = text("""
            SELECT 
                tsn.source_identity_id, 
                tpn.person_id,
                tpn.norm_name,
                a1.assertion_id AS ev1,
                a2.assertion_id AS ev2
            FROM temp_source_norm tsn
            JOIN temp_person_norm tpn ON tsn.norm_name = tpn.norm_name
            JOIN civix.assertion a1 ON a1.subject_entity_id = tsn.source_identity_id 
                AND a1.predicate = 'OWNS'
            JOIN civix.assertion a2 ON a2.subject_entity_id = tpn.person_id 
                AND a2.predicate = 'OWNS'
                AND a1.object_entity_id = a2.object_entity_id
            JOIN civix.phone_number ph ON ph.entity_id = a1.object_entity_id
        """)
        result = await self.session.execute(query)
        candidates = []
        for row in result:
            # Common name check not strictly required for Name+Phone as phone is strong,
            # but we can preserve conflicts if we want.
            candidates.append({
                "source_identity_id": row.source_identity_id,
                "proposed_person_id": row.person_id,
                "analysis_run_id": analysis_run_id,
                "rule_id": "RULE_01_NAME_PHONE",
                "signals": ["NAME_EXACT", "SHARED_PHONE"],
                "evidence_ids": [row.ev1, row.ev2]
            })
        return await self._upsert_candidates(candidates)

    async def _run_rule_name_account(self, analysis_run_id: UUID) -> int:
        """
        RULE_02: Exact Normalized Name + Shared Financial Account
        """
        query = text("""
            SELECT 
                tsn.source_identity_id, 
                tpn.person_id,
                a1.assertion_id AS ev1,
                a2.assertion_id AS ev2
            FROM temp_source_norm tsn
            JOIN temp_person_norm tpn ON tsn.norm_name = tpn.norm_name
            JOIN civix.assertion a1 ON a1.subject_entity_id = tsn.source_identity_id 
                AND a1.predicate = 'HOLDS_ACCOUNT'
            JOIN civix.assertion a2 ON a2.subject_entity_id = tpn.person_id 
                AND a2.predicate = 'HOLDS_ACCOUNT'
                AND a1.object_entity_id = a2.object_entity_id
            JOIN civix.financial_account fa ON fa.entity_id = a1.object_entity_id
        """)
        result = await self.session.execute(query)
        candidates = []
        for row in result:
            candidates.append({
                "source_identity_id": row.source_identity_id,
                "proposed_person_id": row.person_id,
                "analysis_run_id": analysis_run_id,
                "rule_id": "RULE_02_NAME_ACCOUNT",
                "signals": ["NAME_EXACT", "SHARED_ACCOUNT"],
                "evidence_ids": [row.ev1, row.ev2]
            })
        return await self._upsert_candidates(candidates)

    async def _run_rule_alias_vehicle(self, analysis_run_id: UUID) -> int:
        """
        RULE_03: Alias Match + Shared Vehicle Registration
        """
        query = text("""
            SELECT 
                tsn.source_identity_id, 
                p.entity_id AS person_id,
                a1.assertion_id AS ev1,
                a2.assertion_id AS ev2
            FROM temp_source_norm tsn
            JOIN civix.person_alias pa ON upper(regexp_replace(pa.alias_value, '[^a-zA-Z0-9]', '', 'g')) = tsn.norm_name
            JOIN civix.person p ON pa.person_id = p.entity_id
            JOIN civix.assertion a1 ON a1.subject_entity_id = tsn.source_identity_id 
                AND a1.predicate = 'OWNS'
            JOIN civix.assertion a2 ON a2.subject_entity_id = p.entity_id 
                AND a2.predicate = 'OWNS'
                AND a1.object_entity_id = a2.object_entity_id
            JOIN civix.vehicle v ON v.entity_id = a1.object_entity_id
        """)
        result = await self.session.execute(query)
        candidates = []
        for row in result:
            candidates.append({
                "source_identity_id": row.source_identity_id,
                "proposed_person_id": row.person_id,
                "analysis_run_id": analysis_run_id,
                "rule_id": "RULE_03_ALIAS_VEHICLE",
                "signals": ["ALIAS_MATCH", "SHARED_VEHICLE"],
                "evidence_ids": [row.ev1, row.ev2]
            })
        return await self._upsert_candidates(candidates)

    async def _run_rule_name_org(self, analysis_run_id: UUID) -> int:
        """
        RULE_04: Exact Normalized Name + Shared Organization
        Must protect against common-name collisions.
        """
        # For simplicity, we assume 'EMPLOYED_BY' or similar predicate for Organization
        query = text("""
            SELECT 
                tsn.source_identity_id, 
                tpn.person_id,
                tpn.norm_name,
                a1.assertion_id AS ev1,
                a2.assertion_id AS ev2
            FROM temp_source_norm tsn
            JOIN temp_person_norm tpn ON tsn.norm_name = tpn.norm_name
            JOIN civix.assertion a1 ON a1.subject_entity_id = tsn.source_identity_id 
                AND a1.predicate = 'EMPLOYED_BY'
            JOIN civix.assertion a2 ON a2.subject_entity_id = tpn.person_id 
                AND a2.predicate = 'EMPLOYED_BY'
                AND a1.object_entity_id = a2.object_entity_id
            JOIN civix.organization o ON o.entity_id = a1.object_entity_id
        """)
        result = await self.session.execute(query)
        candidates = []
        
        # Load common names dynamically
        common_names_norm = await self._get_common_names(10)
        
        for row in result:
            if row.norm_name in common_names_norm:
                # Rule 04 is too weak for common names.
                continue
                
            candidates.append({
                "source_identity_id": row.source_identity_id,
                "proposed_person_id": row.person_id,
                "analysis_run_id": analysis_run_id,
                "rule_id": "RULE_04_NAME_ORG",
                "signals": ["NAME_EXACT", "SHARED_ORG"],
                "evidence_ids": [row.ev1, row.ev2]
            })
        return await self._upsert_candidates(candidates)
