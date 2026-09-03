"""
CIVIX 2.0 — NLP Entity Mapper
Round 2A

Maps a validated NLPExtractionResult into the existing PostgreSQL schema.
ALL writes happen in a SINGLE transaction — if any INSERT fails,
the entire extraction is rolled back and the artifact stays in its
previous processing_status.

Pipeline (per authorized architecture):
  Validated NLPExtractionResult
      ↓
  analysis_run row
      ↓
  observation row (raw extracted text)
      ↓
  For each entity:
    entity (supertype) + subtype row (person/org/location/vehicle/account)
    source_identity row (raw name → feeds HITL identity resolution)
    extraction row (type=NER)
    provenance row (SOURCE_IDENTITY ← EXTRACTION)
      ↓
  For each relationship:
    assertion row (S-P-O, predicate_enum, POSSIBLE epistemic_status)
    extraction row (type=RELATIONSHIP_EXTRACTION)
    provenance row (ASSERTION ← EXTRACTION)
      ↓
  For each temporal fact:
    event row (occurred_at = TSTZRANGE)
    event_participant rows
      ↓
  COMMIT

INVARIANTS enforced here:
  - authorized_case_ids MUST be set on every assertion (RLS depends on it).
  - epistemic_status = POSSIBLE for all AI-derived assertions (INV-08).
  - source_identity.identifier_type = 'NAME' (source_identity_type_enum).
  - extraction_type cast to extraction_type_enum.
  - No direct Neo4j writes — outbox triggers handle projection.
"""
import json
import logging
import traceback
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4
import hashlib

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from .schema import (
    NLPExtractionResult, ExtractedEntity, ExtractedRelationship, TemporalFact
)

logger = logging.getLogger(__name__)

# Source record type label for NLP-produced records
NLP_RECORD_TYPE = "NLP_EXTRACTION"

# Observer type for AI observations (stored as free text)
AI_OBSERVER_TYPE = "AI_MODEL"

# Analysis run algorithm type (free text field)
NLP_ALGORITHM_TYPE = "NLP_ENTITY_EXTRACTION"


async def map_extraction_to_db(
    session: AsyncSession,
    result: NLPExtractionResult,
    instance_id: UUID,
    case_id: UUID,
    artifact_id: UUID,
    extracted_text: str,
    user_id: UUID,
    nlp_source_id: UUID,
) -> Dict:
    """
    Maps a validated NLPExtractionResult to PostgreSQL rows.

    All writes occur within the caller's transaction.
    The caller is responsible for commit/rollback.

    Returns a summary dict of what was created.
    """
    summary = {
        "analysis_run_id": None,
        "observation_id": None,
        "entities_created": 0,
        "source_identities_created": 0,
        "extractions_created": 0,
        "assertions_created": 0,
        "provenance_rows_created": 0,
        "events_created": 0,
        "warnings": list(result.validation_warnings),
    }

    # Ensure RLS variables are set for this specific transaction
    await session.execute(text(
        "SELECT set_config('app.current_user_id', :uid, true), "
        "set_config('civix.current_user_id', :uid, true)"
    ), {"uid": str(user_id)})

    # -----------------------------------------------------------------------
    # 1. Create analysis_run
    # -----------------------------------------------------------------------
    run_id = uuid4()
    await session.execute(text("""
        INSERT INTO civix.analysis_run (
            run_id, model_name, model_version, algorithm_type,
            algorithm_parameters, started_at, finished_at, initiated_by
        ) VALUES (
            :run_id, :model_name, :model_version, :algo_type,
            CAST(:params AS jsonb), :started, :finished, :uid
        )
    """), {
        "run_id": run_id,
        "model_name": "gemini-3.6-flash",
        "model_version": "1.0",
        "algo_type": NLP_ALGORITHM_TYPE,
        "params": json.dumps({
            "schema_version": result.schema_version,
            "entity_count": len(result.entities),
            "relationship_count": len(result.relationships),
        }),
        "started": datetime.now(timezone.utc),
        "finished": datetime.now(timezone.utc),
        "uid": user_id,
    })
    summary["analysis_run_id"] = str(run_id)

    # -----------------------------------------------------------------------
    # 2. Create observation (raw extracted text)
    # observation.tx_start has a server-side default — no need to pass it
    # -----------------------------------------------------------------------
    obs_id = uuid4()
    obs_text = extracted_text[:50_000] if extracted_text else ""
    await session.execute(text("""
        INSERT INTO civix.observation (
            observation_id, instance_id, observer_type,
            observation_type, observation_text, observed_at
        ) VALUES (
            :oid, :iid, :otype, :obs_type, :obs_text, :obs_at
        )
    """), {
        "oid": obs_id,
        "iid": instance_id,
        "otype": AI_OBSERVER_TYPE,
        "obs_type": "TEXT_EXTRACTION",
        "obs_text": obs_text,
        "obs_at": datetime.now(timezone.utc),
    })
    summary["observation_id"] = str(obs_id)

    # -----------------------------------------------------------------------
    # 3. Map entities
    # local_id → (entity_id, source_identity_entity_id)
    # -----------------------------------------------------------------------
    local_id_to_entity_id: Dict[str, UUID] = {}
    local_id_to_source_identity_id: Dict[str, UUID] = {}

    for ent in result.entities:
        entity_id, si_entity_id = await _create_entity(
            session, ent, instance_id, artifact_id, run_id, nlp_source_id, summary
        )
        if entity_id:
            local_id_to_entity_id[ent.local_id] = entity_id
            # Use source_identity as assertion subject where possible
            local_id_to_source_identity_id[ent.local_id] = si_entity_id or entity_id

    # -----------------------------------------------------------------------
    # 4. Map relationships → assertions
    # -----------------------------------------------------------------------
    for rel in result.relationships:
        subject_id = local_id_to_source_identity_id.get(rel.subject_local_id)
        object_id = local_id_to_entity_id.get(rel.object_local_id)

        if not subject_id or not object_id:
            msg = (
                f"Skipping relationship {rel.predicate}: "
                f"could not resolve subject '{rel.subject_local_id}' "
                f"or object '{rel.object_local_id}'"
            )
            logger.warning(msg)
            summary["warnings"].append(msg)
            continue

        await _create_assertion(
            session, rel, subject_id, object_id,
            instance_id, run_id, case_id, summary
        )

    # -----------------------------------------------------------------------
    # 5. Map temporal facts → events
    # -----------------------------------------------------------------------
    for tf in result.temporal_facts:
        await _create_event(
            session, tf, local_id_to_entity_id, instance_id, summary
        )

    return summary


async def _create_entity(
    session: AsyncSession,
    ent: ExtractedEntity,
    instance_id: UUID,
    artifact_id: UUID,
    run_id: UUID,
    nlp_source_id: UUID,
    summary: Dict,
) -> Tuple[Optional[UUID], Optional[UUID]]:
    """
    Creates: source_record + entity + subtype + source_identity + extraction + provenance.
    Returns (canonical_entity_id, source_identity_entity_id).
    """
    try:
        # --- source_record for this extraction ---
        sr_id = uuid4()
        ent_json = json.dumps({
            "local_id": ent.local_id,
            "name": ent.canonical_name,
            "type": ent.entity_type
        })
        raw_hash = hashlib.sha256(ent_json.encode()).digest()

        await session.execute(text("""
            INSERT INTO civix.source_record (
                source_record_id, source_id, external_reference,
                record_type, raw_content_hash
            ) VALUES (:sr_id, :src_id, :ext_ref, :rtype, :rhash)
        """), {
            "sr_id": sr_id,
            "src_id": nlp_source_id,
            "ext_ref": f"nlp_entity_{artifact_id}_{ent.local_id}",
            "rtype": NLP_RECORD_TYPE,
            "rhash": raw_hash,
        })

        # --- Canonical entity (supertype row) ---
        entity_id = uuid4()
        pg_entity_type = _map_entity_type_to_pg(ent.entity_type)
        await session.execute(text("""
            INSERT INTO civix.entity (entity_id, entity_type, visibility_status)
            VALUES (:eid, CAST(:etype AS civix.entity_type_enum), 'ACTIVE')
        """), {"eid": entity_id, "etype": pg_entity_type})

        # --- Subtype row ---
        await _create_entity_subtype(session, entity_id, ent, summary)
        summary["entities_created"] += 1

        # --- source_identity (raw name → HITL resolution queue) ---
        si_entity_id = uuid4()
        await session.execute(text("""
            INSERT INTO civix.entity (entity_id, entity_type, visibility_status)
            VALUES (:eid, 'SOURCE_IDENTITY', 'ACTIVE')
        """), {"eid": si_entity_id})

        await session.execute(text("""
            INSERT INTO civix.source_identity (
                entity_id, raw_identifier,
                identifier_type, source_record_id, observed_at
            ) VALUES (
                :eid, :raw_id,
                CAST('NAME' AS civix.source_identity_type_enum),
                :srid, :obs_at
            )
        """), {
            "eid": si_entity_id,
            "raw_id": ent.canonical_name,
            "srid": sr_id,
            "obs_at": datetime.now(timezone.utc),
        })
        summary["source_identities_created"] += 1

        # --- extraction row (NER) ---
        ext_id = uuid4()
        extraction_value = {
            "local_id": ent.local_id,
            "entity_type": ent.entity_type,
            "canonical_name": ent.canonical_name,
            "aliases": ent.aliases,
            "attributes": ent.attributes,
            "source_spans": [
                {"page": s.page, "text_snippet": s.text_snippet}
                for s in ent.source_spans
            ],
        }
        await session.execute(text("""
            INSERT INTO civix.extraction (
                extraction_id, instance_id, analysis_run_id,
                extraction_type, extracted_value, ai_confidence
            ) VALUES (
                :ext_id, :iid, :run_id,
                CAST('NER' AS civix.extraction_type_enum),
                CAST(:val AS jsonb), :conf
            )
        """), {
            "ext_id": ext_id,
            "iid": instance_id,
            "run_id": run_id,
            "val": json.dumps(extraction_value),
            "conf": ent.confidence,
        })
        summary["extractions_created"] += 1

        # --- provenance rows ---
        await _insert_provenance(
            session, pg_entity_type, entity_id, "EXTRACTION", ext_id, "AI_NER"
        )
        await _insert_provenance(
            session, "SOURCE_IDENTITY", si_entity_id, "EXTRACTION", ext_id, "AI_NER"
        )
        summary["provenance_rows_created"] += 2

        return entity_id, si_entity_id

    except Exception as e:
        logger.error(
            f"Failed to create entity '{ent.canonical_name}': {e}\n"
            f"{traceback.format_exc()}"
        )
        raise  # caller handles rollback


async def _create_entity_subtype(
    session: AsyncSession,
    entity_id: UUID,
    ent: ExtractedEntity,
    summary: Dict,
):
    """Creates the appropriate subtype row based on entity_type."""
    attrs = ent.attributes or {}

    if ent.entity_type == "PERSON":
        dob_str = attrs.get("date_of_birth")
        from datetime import date
        dob = None
        if dob_str:
            try:
                dob = date.fromisoformat(dob_str)
            except ValueError:
                dob = None

        await session.execute(text("""
            INSERT INTO civix.person (
                entity_id, display_name, date_of_birth, gender, nationality
            ) VALUES (:eid, :name, :dob, :gender, :nat)
        """), {
            "eid": entity_id,
            "name": ent.canonical_name,
            "dob": dob,
            "gender": attrs.get("gender"),
            "nat": (attrs.get("nationality") or "")[:3] or None,
        })

    elif ent.entity_type == "ORGANIZATION":
        # org_type is text (not an enum) in the live schema
        org_type = (attrs.get("org_type") or "OTHER").upper()
        valid_org_types = {"NGO", "COMPANY", "GOVT", "CRIMINAL_NETWORK", "OTHER"}
        if org_type not in valid_org_types:
            org_type = "OTHER"
        await session.execute(text("""
            INSERT INTO civix.organization (
                entity_id, legal_name, org_type, registration_number, jurisdiction
            ) VALUES (:eid, :name, :otype, :regnum, :jur)
        """), {
            "eid": entity_id,
            "name": ent.canonical_name,
            "otype": org_type,
            "regnum": attrs.get("registration_number"),
            "jur": attrs.get("jurisdiction"),
        })

    elif ent.entity_type == "LOCATION":
        lat = attrs.get("latitude")
        lon = attrs.get("longitude")
        if lat is not None and lon is not None:
            try:
                lat_f = float(lat)
                lon_f = float(lon)
                await session.execute(text("""
                    INSERT INTO civix.location (
                        entity_id, location_name, geometry,
                        location_type
                    ) VALUES (
                        :eid, :name,
                        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
                        CAST('EXACT_POINT' AS civix.location_type_enum)
                    )
                """), {
                    "eid": entity_id,
                    "name": ent.canonical_name,
                    "lat": lat_f,
                    "lon": lon_f,
                })
            except (ValueError, TypeError):
                await _insert_location_text_only(session, entity_id, ent.canonical_name)
        else:
            await _insert_location_text_only(session, entity_id, ent.canonical_name)

    elif ent.entity_type == "VEHICLE":
        # vehicle.registration_number has a UNIQUE constraint
        # Use a UUID suffix to guarantee uniqueness if multiple NLP extractions
        # produce the same plate (deduplication is HITL concern)
        reg_raw = (attrs.get("registration_number") or ent.canonical_name or "")[:50]
        if not reg_raw:
            reg_raw = str(entity_id)[:20]

        # Suffix entity_id prefix to break UNIQUE conflicts from same plate extracted
        # across multiple documents (identity resolution will merge later)
        reg_unique = f"{reg_raw}_{str(entity_id)[:8]}"[:50]

        vehicle_type = (attrs.get("vehicle_type") or "OTHER").upper()
        valid_vehicle_types = {"CAR", "TRUCK", "MOTORCYCLE", "AUTO_RICKSHAW", "OTHER"}
        if vehicle_type not in valid_vehicle_types:
            vehicle_type = "OTHER"

        await session.execute(text("""
            INSERT INTO civix.vehicle (
                entity_id, registration_number, make, model, color, vehicle_type
            ) VALUES (:eid, :reg, :make, :model, :color, :vtype)
        """), {
            "eid": entity_id,
            "reg": reg_unique,
            "make": attrs.get("make"),
            "model": attrs.get("model"),
            "color": attrs.get("color"),
            "vtype": vehicle_type,
        })

    elif ent.entity_type == "FINANCIAL_ACCOUNT":
        acct_type = (attrs.get("account_type") or "OTHER").upper()
        valid_acct_types = {"SAVINGS", "CURRENT", "FIXED_DEPOSIT", "WALLET"}
        if acct_type not in valid_acct_types:
            acct_type = "CURRENT"
        masked = (attrs.get("masked_number") or ent.canonical_name or "")[:20]
        await session.execute(text("""
            INSERT INTO civix.financial_account (
                entity_id, masked_number, account_type, bank_name
            ) VALUES (:eid, :masked, :atype, :bank)
        """), {
            "eid": entity_id,
            "masked": masked,
            "atype": acct_type,
            "bank": attrs.get("bank_name"),
        })


async def _insert_location_text_only(
    session: AsyncSession,
    entity_id: UUID,
    name: str,
):
    """Location with unknown coordinates — use zero-point + ESTIMATED_POINT + large uncertainty."""
    await session.execute(text("""
        INSERT INTO civix.location (
            entity_id, location_name, geometry,
            location_type, uncertainty_radius_meters
        ) VALUES (
            :eid, :name,
            ST_SetSRID(ST_MakePoint(0, 0), 4326),
            CAST('ESTIMATED_POINT' AS civix.location_type_enum),
            100000.0
        )
    """), {"eid": entity_id, "name": name})


async def _create_assertion(
    session: AsyncSession,
    rel: ExtractedRelationship,
    subject_entity_id: UUID,
    object_entity_id: UUID,
    instance_id: UUID,
    run_id: UUID,
    case_id: UUID,
    summary: Dict,
):
    """Creates assertion + extraction + provenance for a validated relationship."""
    try:
        assertion_id = uuid4()

        await session.execute(text("""
            INSERT INTO civix.assertion (
                assertion_id, subject_entity_id,
                predicate,
                object_entity_id, epistemic_status,
                ai_confidence, source_analysis_run_id,
                authorized_case_ids
            ) VALUES (
                :aid, :subject,
                CAST(:pred AS civix.predicate_enum),
                :object,
                CAST('POSSIBLE' AS civix.epistemic_status_enum),
                :conf, :run_id,
                ARRAY[:case_id]::uuid[]
            )
        """), {
            "aid": assertion_id,
            "subject": subject_entity_id,
            "pred": rel.predicate,
            "object": object_entity_id,
            "conf": rel.confidence,
            "run_id": run_id,
            "case_id": case_id,
        })
        summary["assertions_created"] += 1

        # Extraction row for the relationship
        ext_id = uuid4()
        extraction_value = {
            "predicate": rel.predicate,
            "subject_local_id": rel.subject_local_id,
            "object_local_id": rel.object_local_id,
            "source_spans": [
                {"page": s.page, "text_snippet": s.text_snippet}
                for s in rel.source_spans
            ],
        }
        await session.execute(text("""
            INSERT INTO civix.extraction (
                extraction_id, instance_id, analysis_run_id,
                extraction_type, extracted_value, ai_confidence
            ) VALUES (
                :ext_id, :iid, :run_id,
                CAST('RELATIONSHIP_EXTRACTION' AS civix.extraction_type_enum),
                CAST(:val AS jsonb), :conf
            )
        """), {
            "ext_id": ext_id,
            "iid": instance_id,
            "run_id": run_id,
            "val": json.dumps(extraction_value),
            "conf": rel.confidence,
        })
        summary["extractions_created"] += 1

        # Provenance: ASSERTION ← EXTRACTION
        await _insert_provenance(
            session, "ASSERTION", assertion_id, "EXTRACTION", ext_id, "AI_REL_EXTRACT"
        )
        summary["provenance_rows_created"] += 1

    except Exception as e:
        logger.error(f"Failed to create assertion {rel.predicate}: {e}")
        raise


async def _create_event(
    session: AsyncSession,
    tf: TemporalFact,
    local_id_to_entity_id: Dict[str, UUID],
    instance_id: UUID,
    summary: Dict,
):
    """Creates an event + event_participant rows for a temporal fact."""
    try:
        event_id = uuid4()

        # Build TSTZRANGE from date/time
        if tf.event_date:
            try:
                if tf.event_time:
                    lower_dt = f"{tf.event_date}T{tf.event_time}+00"
                    upper_dt = f"{tf.event_date}T{tf.event_time}+00"
                else:
                    lower_dt = f"{tf.event_date}T00:00:00+00"
                    upper_dt = f"{tf.event_date}T23:59:59+00"
                tsrange = f"[{lower_dt},{upper_dt}]"
            except Exception:
                tsrange = "[now,now]"
        else:
            tsrange = "[now,now]"

        await session.execute(text("""
            INSERT INTO civix.event (
                event_id,
                event_type,
                occurred_at,
                description
            ) VALUES (
                :eid,
                CAST('OTHER' AS civix.event_type_enum),
                CAST(:occurred AS text)::tstzrange,
                :desc
            )
        """), {
            "eid": event_id,
            "occurred": tsrange,
            "desc": tf.event_description[:500],
        })
        summary["events_created"] += 1

        # Event participants — participant_role is participant_role_enum
        for local_id in tf.involved_entity_local_ids:
            entity_id = local_id_to_entity_id.get(local_id)
            if not entity_id:
                continue
            try:
                await session.execute(text("""
                    INSERT INTO civix.event_participant (
                        participant_id, event_id, entity_id,
                        participant_role
                    ) VALUES (
                        :pid, :eid, :entity_id,
                        CAST('PARTICIPANT' AS civix.participant_role_enum)
                    )
                    ON CONFLICT ON CONSTRAINT uq_event_participant DO NOTHING
                """), {
                    "pid": uuid4(),
                    "eid": event_id,
                    "entity_id": entity_id,
                })
            except Exception as ep:
                logger.warning(f"Event participant insert failed (non-fatal): {ep}")

    except Exception as e:
        logger.warning(
            f"Failed to create event for temporal fact '{tf.event_description[:50]}': {e}"
        )
        # Events are non-critical — log and continue, do not re-raise


async def _insert_provenance(
    session: AsyncSession,
    derived_type: str,
    derived_id: UUID,
    source_type: str,
    source_id: UUID,
    derivation_method: str,
):
    """Inserts a provenance record linking derived artifact to its source."""
    prov_id = uuid4()
    await session.execute(text("""
        INSERT INTO civix.provenance (
            provenance_id, derived_type, derived_id,
            source_type, source_id, derivation_method
        ) VALUES (:pid, :dtype, :did, :stype, :sid, :method)
    """), {
        "pid": prov_id,
        "dtype": derived_type,
        "did": derived_id,
        "stype": source_type,
        "sid": source_id,
        "method": derivation_method,
    })


def _map_entity_type_to_pg(entity_type: str) -> str:
    """Maps NLP schema entity type strings to civix.entity_type_enum values."""
    mapping = {
        "PERSON": "PERSON",
        "ORGANIZATION": "ORGANIZATION",
        "LOCATION": "LOCATION",
        "VEHICLE": "VEHICLE",
        "FINANCIAL_ACCOUNT": "FINANCIAL_ACCOUNT",
    }
    return mapping.get(entity_type, "SOURCE_IDENTITY")
