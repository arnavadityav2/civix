"""
CIVIX 2.0 — NLP Extraction Schema
Round 2A

Defines the structured output schema that the LLM must produce,
and the internal Python dataclasses used throughout the NLP pipeline.

The LLM is an extraction engine — it produces an Untrusted JSON blob.
This module defines what a valid, trusted NLPExtractionResult looks like
AFTER passing through the validator.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

# ---------------------------------------------------------------------------
# Allowed entity types (must match civix.entity_type_enum)
# ---------------------------------------------------------------------------
ALLOWED_ENTITY_TYPES = {
    "PERSON", "ORGANIZATION", "LOCATION", "VEHICLE", "FINANCIAL_ACCOUNT"
}

# ---------------------------------------------------------------------------
# Allowed predicates for LLM extraction
# (subset of civix.predicate_enum — only those an LLM can reasonably extract
# from document text; CDR/transaction-specific predicates excluded)
# ---------------------------------------------------------------------------
ALLOWED_PREDICATES = {
    "SEEN_AT",
    "PRESENT_AT",
    "OWNS",
    "OWNED",
    "EMPLOYED_BY",
    "KNOWN_ASSOCIATE_OF",
    "RESIDED_AT",
    "VISITED",
    "MEMBER_OF",
    "REGISTERED_TO",
    "DRIVER_OF",
    "PASSENGER_IN",
    "TRANSFERRED_TO",
    "HOLDS_ACCOUNT",
    "LOCATED_AT",
    "REGISTERED_AT",
    "DNA_MATCHES",
    "FINGERPRINT_MATCHES",
    "FACE_MATCHES",
    "VEHICLE_REG_MATCHES",
    "TIME_OF_DEATH_IS",
    "CAUSE_OF_DEATH_IS",
    "HAS_INJURY",
}

# Minimum confidence threshold — items below this are dropped
MIN_CONFIDENCE = 0.25


# ---------------------------------------------------------------------------
# Internal data structures (post-validation)
# ---------------------------------------------------------------------------

@dataclass
class SourceSpan:
    """Reference back to where in the document a claim was found."""
    page: Optional[int]       # 1-indexed; None for non-paged documents
    text_snippet: str         # Surrounding text context


@dataclass
class ExtractedEntity:
    """A validated entity extracted by the LLM."""
    local_id: str             # Temporary ID for cross-referencing within the document
    entity_type: str          # PERSON, ORGANIZATION, LOCATION, VEHICLE, FINANCIAL_ACCOUNT
    canonical_name: str       # Primary name/identifier
    aliases: List[str]        # Alternative names
    attributes: Dict[str, Any]  # Type-specific attributes
    confidence: float
    source_spans: List[SourceSpan]


@dataclass
class ExtractedRelationship:
    """A validated relationship extracted by the LLM."""
    subject_local_id: str
    predicate: str            # Must be in ALLOWED_PREDICATES
    object_local_id: str
    confidence: float
    source_spans: List[SourceSpan]


@dataclass
class TemporalFact:
    """A temporal claim extracted by the LLM."""
    event_description: str
    event_date: Optional[str]   # ISO 8601 date string or None
    event_time: Optional[str]   # HH:MM:SS or None
    temporal_precision: str     # MINUTE, HOUR, DAY, MONTH, YEAR, APPROXIMATE
    involved_entity_local_ids: List[str]
    source_spans: List[SourceSpan]


@dataclass
class NLPExtractionResult:
    """
    The fully validated, trusted output of the NLP pipeline.
    This is what the entity_mapper receives — Gemini's raw output is NEVER
    passed directly to the mapper.
    """
    schema_version: str
    entities: List[ExtractedEntity] = field(default_factory=list)
    relationships: List[ExtractedRelationship] = field(default_factory=list)
    temporal_facts: List[TemporalFact] = field(default_factory=list)
    validation_warnings: List[str] = field(default_factory=list)  # Non-fatal issues logged
    raw_token_count: int = 0


# ---------------------------------------------------------------------------
# LLM Output Schema (the JSON template we send to Gemini as a constraint)
# ---------------------------------------------------------------------------

LLM_OUTPUT_SCHEMA_DESCRIPTION = """
Return ONLY a JSON object with this exact structure. No prose, no markdown fences.

{
  "schema_version": "1.0",
  "entities": [
    {
      "local_id": "E001",
      "type": "PERSON | ORGANIZATION | LOCATION | VEHICLE | FINANCIAL_ACCOUNT",
      "canonical_name": "string — primary name or identifier",
      "aliases": ["list of alternative names/spellings"],
      "attributes": {
        // For PERSON: date_of_birth (YYYY-MM-DD or null), gender (MALE/FEMALE/OTHER/null), nationality (3-char ISO or null)
        // For VEHICLE: registration_number, make, model, color, vehicle_type (CAR/TRUCK/MOTORCYCLE/OTHER)
        // For FINANCIAL_ACCOUNT: masked_number, account_type (SAVINGS/CURRENT/WALLET/OTHER), bank_name
        // For ORGANIZATION: legal_name, org_type (NGO/COMPANY/GOVT/CRIMINAL_NETWORK/OTHER), registration_number
        // For LOCATION: address, location_text, latitude (float or null), longitude (float or null)
      },
      "confidence": 0.0,
      "source_spans": [{"page": null_or_int, "text_snippet": "surrounding text context"}]
    }
  ],
  "relationships": [
    {
      "subject_local_id": "E001",
      "predicate": "one of: SEEN_AT, PRESENT_AT, OWNS, OWNED, EMPLOYED_BY, KNOWN_ASSOCIATE_OF, RESIDED_AT, VISITED, MEMBER_OF, REGISTERED_TO, DRIVER_OF, PASSENGER_IN, TRANSFERRED_TO, HOLDS_ACCOUNT, LOCATED_AT, REGISTERED_AT, DNA_MATCHES, FINGERPRINT_MATCHES, FACE_MATCHES, VEHICLE_REG_MATCHES, TIME_OF_DEATH_IS, CAUSE_OF_DEATH_IS, HAS_INJURY",
      "object_local_id": "E002",
      "confidence": 0.0,
      "source_spans": [{"page": null_or_int, "text_snippet": "surrounding text context"}]
    }
  ],
  "temporal_facts": [
    {
      "event_description": "description of the event",
      "event_date": "YYYY-MM-DD or null",
      "event_time": "HH:MM:SS or null",
      "temporal_precision": "MINUTE | HOUR | DAY | MONTH | YEAR | APPROXIMATE",
      "involved_entity_local_ids": ["E001"],
      "source_spans": [{"page": null_or_int, "text_snippet": "surrounding text"}]
    }
  ]
}

RULES:
- Only use predicates from the explicit list above. Do NOT invent predicates.
- Only extract what is EXPLICITLY stated. Do NOT infer relationships.
- KNOWN_ASSOCIATE_OF may be used between a PERSON and an ORGANIZATION if they are explicitly described as an 'associate of' the organization.
- Set confidence = 0.0 for uncertain items (do NOT omit them).
- local_id values must be unique strings (E001, E002, ...).
- source_spans text_snippet should be 50-200 chars of surrounding text.
- If no entities are found, return empty arrays — not null.
"""
