"""
CIVIX 2.0 — Evidence Processing Pipeline (Background)
Round 2A

Orchestrates the full evidence processing lifecycle:
  STORED → TEXT_EXTRACTED → NLP_ANALYZED → COMPLETED
  (with FAILED_* states on errors)

This module is called as a FastAPI BackgroundTask — it runs after
the HTTP response has been sent (202 Accepted).

Key invariant: The artifact file and artifact row always exist.
If any processing stage fails, the artifact remains with a FAILED_*
status and processing_error set. It can be retried by calling
POST /evidence/{artifact_id}/process again.
"""
import json
import logging
import traceback
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from civix_api.services.evidence_store import retrieve_file
from civix_api.services.processors import ProcessorResolver
from civix_api.services.nlp.gemini_client import call_gemini, GeminiCallError
from civix_api.services.nlp.groq_client import call_groq, GroqCallError
from civix_api.services.nlp.validator import validate, NLPValidationError
from civix_api.services.nlp.entity_mapper import map_extraction_to_db

logger = logging.getLogger(__name__)

# We need a fresh DB session for background tasks (not the request-scoped one)
# This import is done inline to avoid circular imports.


async def run_evidence_pipeline(
    artifact_id: UUID,
    instance_id: UUID,
    case_id: UUID,
    case_context: str,
    storage_uri: str,
    original_filename: str,
    user_id: UUID,
    nlp_source_id: UUID,
    mock_llm_response: Optional[str] = None,
):
    """
    Background pipeline for a single evidence artifact.

    Creates its own DB session (not request-scoped).
    Updates processing_status at each stage.
    Any unhandled exception leaves the artifact in a FAILED_* state.
    """
    from civix_api.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        try:
            logger.info(f"[Pipeline] Starting for artifact {artifact_id}")

            # -----------------------------------------------------------------
            # Establish RLS context for this background session.
            # The pipeline creates its own DB connection (not request-scoped),
            # so we must explicitly set app.current_user_id for every RLS-
            # protected INSERT/UPDATE to work correctly.
            # -----------------------------------------------------------------
            await session.execute(text(
                "SELECT set_config('app.current_user_id', :uid, false), "
                "set_config('civix.current_user_id', :uid, false)"
            ), {"uid": str(user_id)})
            await session.commit()

            # -----------------------------------------------------------------
            # Stage 1: PROCESSING
            # -----------------------------------------------------------------
            await _update_status(session, artifact_id, "PROCESSING")

            # -----------------------------------------------------------------
            # Stage 2: Text / Metadata Extraction
            # -----------------------------------------------------------------
            try:
                file_bytes = retrieve_file(storage_uri)
            except FileNotFoundError as e:
                await _fail(session, artifact_id, "FAILED_EXTRACTION",
                            f"Evidence file not found on disk: {e}")
                return

            mime_type, processor_result = ProcessorResolver.resolve(
                file_bytes, original_filename
            )

            if not processor_result.success:
                # Unsupported MIME or fatal extraction error
                if "Unsupported file type" in (processor_result.error or ""):
                    await _fail(session, artifact_id, "UNSUPPORTED", processor_result.error)
                else:
                    await _fail(session, artifact_id, "FAILED_EXTRACTION", processor_result.error)
                return

            # Store media_metadata on the artifact
            await session.execute(text("""
                UPDATE civix.evidence_artifact
                SET media_metadata = CAST(:meta AS jsonb),
                    processing_status = 'TEXT_EXTRACTED'
                WHERE artifact_id = :aid
            """), {
                "aid": artifact_id,
                "meta": json.dumps(processor_result.media_metadata),
            })
            await session.commit()
            logger.info(f"[Pipeline] Text extraction complete for {artifact_id}")

            # -----------------------------------------------------------------
            # Stage 3: NLP Extraction (Gemini)
            # -----------------------------------------------------------------
            await _update_status(session, artifact_id, "NLP_ANALYZED")

            extracted_text = processor_result.extracted_text or ""

            if not extracted_text.strip() and not processor_result.requires_ocr:
                # No text to analyze (not an OCR case — truly empty or unsupported for NLP)
                logger.info(f"[Pipeline] No text content for NLP — marking COMPLETED.")
                await _complete(session, artifact_id)
                return

            try:
                import os
                if os.environ.get("CIVIX_USE_GROQ_PROVIDER") == "1":
                    raw_json_chunks = call_groq(
                        extracted_text=extracted_text,
                        case_context=case_context,
                        mock_response=mock_llm_response,
                    )
                else:
                    raw_json_chunks = call_gemini(
                        extracted_text=extracted_text,
                        case_context=case_context,
                        mock_response=mock_llm_response,
                    )
            except (GeminiCallError, GroqCallError) as e:
                await _fail(session, artifact_id, "FAILED_NLP", str(e))
                return

            # -----------------------------------------------------------------
            # Stage 4: Validate + Map → PostgreSQL
            # -----------------------------------------------------------------
            total_summary = {
                "entities_created": 0,
                "assertions_created": 0,
                "events_created": 0,
                "extractions_created": 0,
                "provenance_rows_created": 0,
                "warnings": [],
                "chunks_processed": 0,
                "chunks_failed": 0,
            }

            for chunk_idx, raw_json in enumerate(raw_json_chunks):
                try:
                    validated_result = validate(raw_json)
                except NLPValidationError as ve:
                    logger.error(f"[Pipeline] Chunk {chunk_idx} validation failed: {ve}")
                    total_summary["chunks_failed"] += 1
                    continue

                # Map to DB within a single transaction per chunk
                try:
                    chunk_summary = await map_extraction_to_db(
                        session=session,
                        result=validated_result,
                        instance_id=instance_id,
                        case_id=case_id,
                        artifact_id=artifact_id,
                        extracted_text=extracted_text if chunk_idx == 0 else "",
                        user_id=user_id,
                        nlp_source_id=nlp_source_id,
                    )
                    await session.commit()
                    total_summary["chunks_processed"] += 1

                    # Accumulate
                    for k in ("entities_created", "assertions_created", "events_created",
                              "extractions_created", "provenance_rows_created"):
                        total_summary[k] = total_summary.get(k, 0) + chunk_summary.get(k, 0)
                    total_summary["warnings"].extend(chunk_summary.get("warnings", []))

                    logger.info(
                        f"[Pipeline] Chunk {chunk_idx + 1}: "
                        f"{chunk_summary['entities_created']} entities, "
                        f"{chunk_summary['assertions_created']} assertions"
                    )

                except Exception as e:
                    await session.rollback()
                    logger.error(
                        f"[Pipeline] DB mapping failed for chunk {chunk_idx}: {e}\n"
                        f"{traceback.format_exc()}"
                    )
                    total_summary["chunks_failed"] += 1

            # If ALL chunks failed to map → FAILED_MAPPING
            if total_summary["chunks_failed"] > 0 and total_summary["chunks_processed"] == 0:
                await _fail(session, artifact_id, "FAILED_MAPPING",
                            f"All {total_summary['chunks_failed']} chunk(s) failed to map.")
                return

            # -----------------------------------------------------------------
            # Stage 5: COMPLETED
            # -----------------------------------------------------------------
            await _complete(session, artifact_id)

            logger.info(
                f"[Pipeline] COMPLETED artifact {artifact_id}: "
                f"{total_summary['entities_created']} entities, "
                f"{total_summary['assertions_created']} assertions, "
                f"{total_summary['events_created']} events, "
                f"{total_summary['provenance_rows_created']} provenance rows."
            )

        except Exception as e:
            # Catch-all — should not reach here if individual stages handle errors
            try:
                await session.rollback()
                await _fail(
                    session, artifact_id, "FAILED_MAPPING",
                    f"Unexpected pipeline error: {e}\n{traceback.format_exc()}"
                )
            except Exception:
                logger.critical(f"[Pipeline] Failed to record failure state for {artifact_id}: {e}")


async def _update_status(session: AsyncSession, artifact_id: UUID, status: str):
    await session.execute(text("""
        UPDATE civix.evidence_artifact
        SET processing_status = :status
        WHERE artifact_id = :aid
    """), {"aid": artifact_id, "status": status})
    await session.commit()


async def _fail(session: AsyncSession, artifact_id: UUID, status: str, error: str):
    logger.error(f"[Pipeline] {status} for artifact {artifact_id}: {error[:500]}")
    await session.execute(text("""
        UPDATE civix.evidence_artifact
        SET processing_status = :status,
            processing_error = :error,
            processed_at = :now
        WHERE artifact_id = :aid
    """), {
        "aid": artifact_id,
        "status": status,
        "error": (error or "")[:5000],
        "now": datetime.now(timezone.utc),
    })
    await session.commit()


async def _complete(session: AsyncSession, artifact_id: UUID):
    await session.execute(text("""
        UPDATE civix.evidence_artifact
        SET processing_status = 'COMPLETED',
            processed_at = :now,
            processing_error = NULL
        WHERE artifact_id = :aid
    """), {"aid": artifact_id, "now": datetime.now(timezone.utc)})
    await session.commit()


async def ensure_nlp_source_exists(session: AsyncSession) -> UUID:
    """
    Ensures a civix.source row exists for the NLP processing system.
    Returns its source_id.
    """
    result = await session.execute(text("""
        SELECT source_id FROM civix.source WHERE source_name = 'CIVIX_NLP_PIPELINE'
    """))
    row = result.first()
    if row:
        return row[0]

    source_id = uuid4()
    await session.execute(text("""
        INSERT INTO civix.source (source_id, source_name, agency_type, reliability_score, jurisdiction)
        VALUES (:sid, 'CIVIX_NLP_PIPELINE', 'OTHER', 0.70, 'SYSTEM')
        ON CONFLICT (source_name) DO NOTHING
    """), {"sid": source_id})
    await session.commit()

    # Re-fetch in case of conflict
    result = await session.execute(text("""
        SELECT source_id FROM civix.source WHERE source_name = 'CIVIX_NLP_PIPELINE'
    """))
    return result.scalar()
