"""
CIVIX 2.0 — NLP Output Validator
Round 2A

Validates raw LLM JSON output against the NLPExtractionResult schema.
Drops invalid items with warnings rather than failing the entire extraction.
Only raises NLPValidationError if the JSON is completely unparseable or
if the schema_version is missing.

The validator is the CRITICAL trust boundary between the LLM and PostgreSQL.
Nothing in the LLM output bypasses this layer.
"""
import json
import logging
from typing import Any, Dict, List, Optional

from .schema import (
    NLPExtractionResult, ExtractedEntity, ExtractedRelationship,
    TemporalFact, SourceSpan,
    ALLOWED_ENTITY_TYPES, ALLOWED_PREDICATES, MIN_CONFIDENCE,
)

logger = logging.getLogger(__name__)


class NLPValidationError(Exception):
    """Raised when the LLM output is fundamentally unparseable."""
    pass


def _parse_source_spans(raw_spans: Any) -> List[SourceSpan]:
    spans = []
    if not isinstance(raw_spans, list):
        return spans
    for s in raw_spans:
        if not isinstance(s, dict):
            continue
        page = s.get("page")
        snippet = s.get("text_snippet", "")
        if isinstance(snippet, str) and snippet.strip():
            spans.append(SourceSpan(
                page=int(page) if isinstance(page, (int, float)) else None,
                text_snippet=snippet[:500],  # Cap snippet length
            ))
    return spans


def validate(raw_llm_output: str) -> NLPExtractionResult:
    """
    Parses and validates raw LLM JSON output.

    Returns a validated NLPExtractionResult.
    Raises NLPValidationError if JSON is unparseable or schema_version is missing.
    Non-fatal issues are logged as warnings and collected in result.validation_warnings.
    """
    warnings: List[str] = []

    # --- Step 1: Parse JSON ---
    try:
        data = json.loads(raw_llm_output.strip())
    except json.JSONDecodeError as e:
        raise NLPValidationError(f"LLM output is not valid JSON: {e}\nRaw: {raw_llm_output[:500]}")

    if not isinstance(data, dict):
        raise NLPValidationError(f"LLM output must be a JSON object, got: {type(data)}")

    # --- Step 2: Schema version ---
    schema_version = data.get("schema_version")
    if not schema_version:
        raise NLPValidationError("LLM output missing required 'schema_version' field.")

    # --- Step 3: Validate entities ---
    raw_entities = data.get("entities", [])
    if not isinstance(raw_entities, list):
        warnings.append("'entities' is not a list — treating as empty.")
        raw_entities = []

    entities: List[ExtractedEntity] = []
    seen_local_ids = set()

    for i, ent in enumerate(raw_entities):
        if not isinstance(ent, dict):
            warnings.append(f"Entity [{i}] is not a dict — skipped.")
            continue

        local_id = ent.get("local_id", f"AUTO_{i}")
        if local_id in seen_local_ids:
            warnings.append(f"Duplicate local_id '{local_id}' — second occurrence skipped.")
            continue
        seen_local_ids.add(local_id)

        entity_type = str(ent.get("type", "")).upper()
        if entity_type not in ALLOWED_ENTITY_TYPES:
            warnings.append(f"Entity '{local_id}': unknown type '{entity_type}' — skipped.")
            continue

        canonical_name = str(ent.get("canonical_name", "")).strip()
        if not canonical_name:
            warnings.append(f"Entity '{local_id}': empty canonical_name — skipped.")
            continue

        confidence = float(ent.get("confidence", 0.0))
        if confidence < MIN_CONFIDENCE:
            warnings.append(
                f"Entity '{local_id}' ({canonical_name}): confidence {confidence:.2f} "
                f"below threshold {MIN_CONFIDENCE} — skipped."
            )
            continue

        aliases_raw = ent.get("aliases", [])
        aliases = [str(a).strip() for a in aliases_raw if isinstance(a, str) and a.strip()]

        attributes = ent.get("attributes", {})
        if not isinstance(attributes, dict):
            attributes = {}

        entities.append(ExtractedEntity(
            local_id=local_id,
            entity_type=entity_type,
            canonical_name=canonical_name,
            aliases=aliases,
            attributes=attributes,
            confidence=min(max(confidence, 0.0), 1.0),
            source_spans=_parse_source_spans(ent.get("source_spans")),
        ))

    # --- Step 4: Validate relationships ---
    raw_rels = data.get("relationships", [])
    if not isinstance(raw_rels, list):
        warnings.append("'relationships' is not a list — treating as empty.")
        raw_rels = []

    relationships: List[ExtractedRelationship] = []

    for i, rel in enumerate(raw_rels):
        if not isinstance(rel, dict):
            warnings.append(f"Relationship [{i}] is not a dict — skipped.")
            continue

        subject_id = rel.get("subject_local_id", "")
        object_id = rel.get("object_local_id", "")
        predicate = str(rel.get("predicate", "")).upper().strip()

        if predicate not in ALLOWED_PREDICATES:
            warnings.append(f"Relationship [{i}]: predicate '{predicate}' not in allowlist — skipped.")
            continue

        # Validate endpoints exist in our entity list
        valid_ids = seen_local_ids
        if subject_id not in valid_ids:
            warnings.append(f"Relationship [{i}]: subject '{subject_id}' not in entity list — skipped.")
            continue
        if object_id not in valid_ids:
            warnings.append(f"Relationship [{i}]: object '{object_id}' not in entity list — skipped.")
            continue

        confidence = float(rel.get("confidence", 0.0))
        if confidence < MIN_CONFIDENCE:
            warnings.append(f"Relationship [{i}] ({predicate}): confidence {confidence:.2f} below threshold — skipped.")
            continue

        relationships.append(ExtractedRelationship(
            subject_local_id=subject_id,
            predicate=predicate,
            object_local_id=object_id,
            confidence=min(max(confidence, 0.0), 1.0),
            source_spans=_parse_source_spans(rel.get("source_spans")),
        ))

    # --- Step 5: Validate temporal facts ---
    raw_temporal = data.get("temporal_facts", [])
    if not isinstance(raw_temporal, list):
        warnings.append("'temporal_facts' is not a list — treating as empty.")
        raw_temporal = []

    temporal_facts: List[TemporalFact] = []
    valid_ids = seen_local_ids

    for i, tf in enumerate(raw_temporal):
        if not isinstance(tf, dict):
            warnings.append(f"TemporalFact [{i}] is not a dict — skipped.")
            continue

        description = str(tf.get("event_description", "")).strip()
        if not description:
            warnings.append(f"TemporalFact [{i}]: empty description — skipped.")
            continue

        precision = str(tf.get("temporal_precision", "APPROXIMATE")).upper()
        if precision not in ("MINUTE", "HOUR", "DAY", "MONTH", "YEAR", "APPROXIMATE"):
            precision = "APPROXIMATE"

        involved_ids_raw = tf.get("involved_entity_local_ids", [])
        involved_ids = [eid for eid in involved_ids_raw if eid in valid_ids]

        temporal_facts.append(TemporalFact(
            event_description=description,
            event_date=tf.get("event_date"),
            event_time=tf.get("event_time"),
            temporal_precision=precision,
            involved_entity_local_ids=involved_ids,
            source_spans=_parse_source_spans(tf.get("source_spans")),
        ))

    # --- Log summary ---
    logger.info(
        f"NLP Validation complete: {len(entities)} entities, "
        f"{len(relationships)} relationships, {len(temporal_facts)} temporal facts. "
        f"{len(warnings)} warning(s)."
    )
    for w in warnings:
        logger.warning(f"  NLP Validation Warning: {w}")

    return NLPExtractionResult(
        schema_version=str(schema_version),
        entities=entities,
        relationships=relationships,
        temporal_facts=temporal_facts,
        validation_warnings=warnings,
    )
