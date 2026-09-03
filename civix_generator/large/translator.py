import os
import datetime
from typing import Dict, Any, List
from .seeds import make_uuid

def translate_evidence(manifests: Dict[str, Any], role_resolver, seed: int, output_dir: str):
    """
    Translates Gemini evidence constraints into exact Parquet records.
    """
    from .writer import ShardWriter
    
    constraints = manifests.get("evidence", {}).get("constraints", [])
    if not constraints:
        return
        
    # Initialize writers
    aw = ShardWriter(output_dir, "evidence_artifact", shard_prefix="planted_")
    iw = ShardWriter(output_dir, "evidence_instance", shard_prefix="planted_")
    ow = ShardWriter(output_dir, "observation", shard_prefix="planted_")
    ew = ShardWriter(output_dir, "events", shard_prefix="planted_")
    pw = ShardWriter(output_dir, "event_participants", shard_prefix="planted_")
    sw = ShardWriter(output_dir, "assertions", shard_prefix="planted_")
    
    cw = ShardWriter(output_dir, "cdrs", partition_keys=["year", "month"], shard_prefix="planted_")
    
    artifacts = []
    instances = []
    observations = []
    events = []
    participants = []
    assertions = []
    cdrs = []
    
    # Base timestamp
    base_t = datetime.datetime(2026, 6, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
    
    # For each constraint, generate the pipeline
    for i, c in enumerate(constraints):
        # 1. Resolve actors
        actor_idx = role_resolver.resolve("DELHI-2026-HL-001", c["actor"])
        target_idx = role_resolver.resolve("DELHI-2026-HL-001", c["target"])
        actor_uuid = make_uuid("civix-large-person", seed, actor_idx)
        target_uuid = make_uuid("civix-large-person", seed, target_idx)
        
        event_time = base_t + datetime.timedelta(hours=c.get("time_offset_hours", 0))
        occurred_at = f"[{event_time.isoformat()}, {(event_time + datetime.timedelta(minutes=5)).isoformat()})"
        
        # Artifact
        artifact_id = make_uuid("civix-demo-artifact", seed, i)
        artifacts.append({
            "artifact_id": artifact_id,
            "sha256_hash": b"DEMO_HASH_" + str(i).encode(),
            "hash_algorithm": "SHA256",
            "mime_type": "text/plain",
            "generation_origin": "MANIFEST_PLANTED"
        })
        
        # Instance
        instance_id = make_uuid("civix-demo-instance", seed, i)
        # Using a dummy case ID for now. Wait, case is DELHI-2026-HL-001
        # The generator uses the case_index. If it's the first case, case_index=0
        case_id = make_uuid("civix-large-case", seed, 0) 
        instances.append({
            "instance_id": instance_id,
            "artifact_id": artifact_id,
            "case_id": case_id,
            "legal_status": "ACTIVE",
            "tx_start": event_time.isoformat(),
            "generation_origin": "MANIFEST_PLANTED"
        })
        
        # Observation
        observation_id = make_uuid("civix-demo-obs", seed, i)
        observations.append({
            "observation_id": observation_id,
            "instance_id": instance_id,
            "observer_type": "AUTOMATED_SYSTEM",
            "observation_text": "Planted telecom observation",
            "observed_at": event_time.isoformat(),
            "tx_start": event_time.isoformat(),
            "generation_origin": "MANIFEST_PLANTED"
        })
        
        # Event
        event_id = make_uuid("civix-demo-event", seed, i)
        events.append({
            "event_id": event_id,
            "event_type": c["event_type"],
            "occurred_at": occurred_at,
            "tx_start": event_time.isoformat(),
            "generation_origin": "MANIFEST_PLANTED"
        })
        
        # Participants
        participants.append({
            "participant_id": make_uuid("civix-demo-part-1", seed, i),
            "event_id": event_id,
            "entity_id": actor_uuid,
            "participant_role": "CALLER",
            "tx_start": event_time.isoformat(),
            "generation_origin": "MANIFEST_PLANTED"
        })
        participants.append({
            "participant_id": make_uuid("civix-demo-part-2", seed, i),
            "event_id": event_id,
            "entity_id": target_uuid,
            "participant_role": "CALLEE",
            "tx_start": event_time.isoformat(),
            "generation_origin": "MANIFEST_PLANTED"
        })
        
        # Assertion
        assertion_id = make_uuid("civix-demo-assert", seed, i)
        assertions.append({
            "assertion_id": assertion_id,
            "subject_entity_id": actor_uuid,
            "predicate": "CONTACTED",
            "object_entity_id": target_uuid,
            "epistemic_status": "OBSERVED",
            "tx_start": event_time.isoformat(),
            "generation_origin": "MANIFEST_PLANTED"
        })
        
        # CDR (so the XGBoost gets it)
        cdr_id = make_uuid("civix-demo-cdr", seed, i)
        # We need phone UUIDs. For demo, we just make up phone IDs based on person indices.
        caller_phone = make_uuid("civix-large-phone", seed, actor_idx)
        callee_phone = make_uuid("civix-large-phone", seed, target_idx)
        cell_id = make_uuid("civix-large-cell", seed, 0)
        
        cdrs.append({
            "cdr_id": cdr_id,
            "caller_phone_id": caller_phone,
            "callee_phone_id": callee_phone,
            "timestamp": event_time.isoformat()[:19],
            "year": event_time.year,
            "month": event_time.month,
            "duration_seconds": 120,
            "call_type": "VOICE",
            "cell_sector_id": cell_id,
            "caller_person_id": actor_uuid,
            "generation_origin": "MANIFEST_PLANTED"
        })

    aw.write_batch(artifacts)
    iw.write_batch(instances)
    ow.write_batch(observations)
    ew.write_batch(events)
    pw.write_batch(participants)
    sw.write_batch(assertions)
    cw.write_batch(cdrs)
    
    aw.close()
    iw.close()
    ow.close()
    ew.close()
    pw.close()
    sw.close()
    cw.close()
    
    print(f"Planted {len(constraints)} manifest constraints into evidence pipeline.")
