import asyncio
import asyncpg
import json
from neo4j import AsyncGraphDatabase

DB_URL = "postgresql://postgres:postgres@localhost:5432/civix_demo"
NEO4J_URI = "bolt://localhost:7688"
NEO4J_USER = "neo4j"
NEO4J_PASS = "password"
BATCH_ID = "remediation_batch_01"

async def project_events(pg, neo4j_session):
    print("Projecting Events...")
    rows = await pg.fetch("SELECT event_id, event_type, occurred_at, description FROM civix.event")
    created = 0
    updated = 0
    for r in rows:
        m = dict(r)
        m = {k: (str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v) for k, v in m.items()}
        res = await neo4j_session.run("""
            MERGE (e:Event {event_id: $event_id})
            ON CREATE SET e += $props, e.remediation_batch_id = $batch, e.remediation_created = true
            ON MATCH SET e += $props, e.remediation_batch_id = $batch, e.remediation_updated = true
            RETURN e.remediation_created AS created
        """, event_id=str(m["event_id"]), props=m, batch=BATCH_ID)
        rec = await res.single()
        if rec and rec["created"]: created += 1
        else: updated += 1
    print(f"Events: {created} created, {updated} updated")

async def project_event_participants(pg, neo4j_session):
    print("Projecting Event Participants...")
    rows = await pg.fetch("SELECT participant_id, event_id, entity_id FROM civix.event_participant")
    created = 0
    updated = 0
    for r in rows:
        res = await neo4j_session.run("""
            MATCH (e:Event {event_id: $event_id})
            MATCH (ent {entity_id: $entity_id})
            MERGE (e)-[rel:PARTICIPATED_AS {participant_id: $participant_id}]->(ent)
            ON CREATE SET rel.remediation_batch_id = $batch, rel.remediation_created = true
            ON MATCH SET rel.remediation_batch_id = $batch, rel.remediation_updated = true
            RETURN rel.remediation_created AS created
        """, event_id=str(r["event_id"]), entity_id=str(r["entity_id"]), participant_id=str(r["participant_id"]), batch=BATCH_ID)
        rec = await res.single()
        if rec and rec["created"]: created += 1
        elif rec: updated += 1
    print(f"Event Participants: {created} created, {updated} updated")

async def project_locations(pg, neo4j_session):
    print("Projecting Locations...")
    rows = await pg.fetch("SELECT entity_id, location_name, location_type FROM civix.location")
    created = 0
    updated = 0
    for r in rows:
        props = {
            "entity_id": str(r["entity_id"]),
            "name": r["location_name"] or "Unknown Location",
            "location_type": r["location_type"]
        }
        res = await neo4j_session.run("""
            MERGE (l:Location {entity_id: $entity_id})
            ON CREATE SET l += $props, l.remediation_batch_id = $batch, l.remediation_created = true
            ON MATCH SET l += $props, l.remediation_batch_id = $batch, l.remediation_updated = true
            RETURN l.remediation_created AS created
        """, entity_id=str(r["entity_id"]), props=props, batch=BATCH_ID)
        rec = await res.single()
        if rec and rec["created"]: created += 1
        elif rec: updated += 1
    print(f"Locations: {created} created, {updated} updated")

async def project_event_locations(pg, neo4j_session):
    print("Projecting Event Locations...")
    rows = await pg.fetch("SELECT event_location_id, event_id, location_id FROM civix.event_location")
    created = 0
    updated = 0
    for r in rows:
        res = await neo4j_session.run("""
            MATCH (e:Event {event_id: $event_id})
            MATCH (l:Location {entity_id: $location_id})
            MERGE (e)-[rel:OCCURRED_AT {event_location_id: $event_location_id}]->(l)
            ON CREATE SET rel.remediation_batch_id = $batch, rel.remediation_created = true
            ON MATCH SET rel.remediation_batch_id = $batch, rel.remediation_updated = true
            RETURN rel.remediation_created AS created
        """, event_id=str(r["event_id"]), location_id=str(r["location_id"]), event_location_id=str(r["event_location_id"]), batch=BATCH_ID)
        rec = await res.single()
        if rec and rec["created"]: created += 1
        elif rec: updated += 1
    print(f"Event Locations: {created} created, {updated} updated")

async def project_evidence(pg, neo4j_session):
    print("Projecting Evidence Artifacts & Instances...")
    # Map artifact_id -> case_id via evidence_instance
    rows = await pg.fetch("""
        SELECT a.artifact_id, a.original_filename, a.mime_type, a.file_size_bytes, a.processing_status, i.instance_id, i.case_id 
        FROM civix.evidence_artifact a
        JOIN civix.evidence_instance i ON a.artifact_id = i.artifact_id
    """)
    nodes_created, nodes_updated = 0, 0
    edges_created, edges_updated = 0, 0
    
    for r in rows:
        artifact_id = str(r["artifact_id"])
        case_id = str(r["case_id"])
        
        props = {
            "artifact_id": artifact_id,
            "name": r["original_filename"] or "Unknown File",
            "mime_type": r["mime_type"],
            "file_size_bytes": r["file_size_bytes"],
            "processing_status": r["processing_status"]
        }
        
        # Merge Node
        res = await neo4j_session.run("""
            MERGE (e:Evidence {artifact_id: $artifact_id})
            ON CREATE SET e += $props, e.remediation_batch_id = $batch, e.remediation_created = true
            ON MATCH SET e += $props, e.remediation_batch_id = $batch, e.remediation_updated = true
            RETURN e.remediation_created AS created
        """, artifact_id=artifact_id, props=props, batch=BATCH_ID)
        rec = await res.single()
        if rec and rec["created"]: nodes_created += 1
        elif rec: nodes_updated += 1
        
        # Merge Edge
        res = await neo4j_session.run("""
            MATCH (c:Case {case_id: $case_id})
            MATCH (e:Evidence {artifact_id: $artifact_id})
            MERGE (c)-[rel:HAS_EVIDENCE]->(e)
            ON CREATE SET rel.remediation_batch_id = $batch, rel.remediation_created = true
            ON MATCH SET rel.remediation_batch_id = $batch, rel.remediation_updated = true
            RETURN rel.remediation_created AS created
        """, case_id=case_id, artifact_id=artifact_id, batch=BATCH_ID)
        rec = await res.single()
        if rec and rec["created"]: edges_created += 1
        elif rec: edges_updated += 1
        
    print(f"Evidence Nodes: {nodes_created} created, {nodes_updated} updated")
    print(f"HAS_EVIDENCE Edges: {edges_created} created, {edges_updated} updated")

async def project_firs(pg, neo4j_session):
    print("Projecting FIRs...")
    rows = await pg.fetch("SELECT fir_id, case_id, fir_number, police_station FROM civix.fir")
    nodes_created, nodes_updated = 0, 0
    edges_created, edges_updated = 0, 0
    
    for r in rows:
        fir_id = str(r["fir_id"])
        case_id = str(r["case_id"])
        props = {
            "fir_id": fir_id,
            "fir_number": r["fir_number"],
            "name": r["fir_number"] or "Unknown FIR",
            "station_name": r["police_station"]
        }
        
        # Merge Node
        res = await neo4j_session.run("""
            MERGE (f:FIR {fir_id: $fir_id})
            ON CREATE SET f += $props, f.remediation_batch_id = $batch, f.remediation_created = true
            ON MATCH SET f += $props, f.remediation_batch_id = $batch, f.remediation_updated = true
            RETURN f.remediation_created AS created
        """, fir_id=fir_id, props=props, batch=BATCH_ID)
        rec = await res.single()
        if rec and rec["created"]: nodes_created += 1
        elif rec: nodes_updated += 1
        
        # Merge Edge
        if case_id and case_id != "None":
            res = await neo4j_session.run("""
                MATCH (c:Case {case_id: $case_id})
                MATCH (f:FIR {fir_id: $fir_id})
                MERGE (c)-[rel:HAS_FIR]->(f)
                ON CREATE SET rel.remediation_batch_id = $batch, rel.remediation_created = true
                ON MATCH SET rel.remediation_batch_id = $batch, rel.remediation_updated = true
                RETURN rel.remediation_created AS created
            """, case_id=case_id, fir_id=fir_id, batch=BATCH_ID)
            rec = await res.single()
            if rec and rec["created"]: edges_created += 1
            elif rec: edges_updated += 1

    print(f"FIR Nodes: {nodes_created} created, {nodes_updated} updated")
    print(f"HAS_FIR Edges: {edges_created} created, {edges_updated} updated")

async def project_leads(pg, neo4j_session):
    print("Projecting Leads...")
    rows = await pg.fetch("SELECT lead_id, case_id, lead_text, priority, status FROM civix.investigative_lead")
    nodes_created, nodes_updated = 0, 0
    edges_created, edges_updated = 0, 0
    
    for r in rows:
        lead_id = str(r["lead_id"])
        case_id = str(r["case_id"])
        props = {
            "lead_id": lead_id,
            "name": r["lead_text"][:50] + "..." if r["lead_text"] else "Unknown Lead",
            "summary": r["lead_text"],
            "priority": r["priority"],
            "status": r["status"]
        }
        
        # Merge Node
        res = await neo4j_session.run("""
            MERGE (l:Lead {lead_id: $lead_id})
            ON CREATE SET l += $props, l.remediation_batch_id = $batch, l.remediation_created = true
            ON MATCH SET l += $props, l.remediation_batch_id = $batch, l.remediation_updated = true
            RETURN l.remediation_created AS created
        """, lead_id=lead_id, props=props, batch=BATCH_ID)
        rec = await res.single()
        if rec and rec["created"]: nodes_created += 1
        elif rec: nodes_updated += 1
        
        # Merge Edge
        if case_id and case_id != "None":
            res = await neo4j_session.run("""
                MATCH (c:Case {case_id: $case_id})
                MATCH (l:Lead {lead_id: $lead_id})
                MERGE (c)-[rel:HAS_LEAD]->(l)
                ON CREATE SET rel.remediation_batch_id = $batch, rel.remediation_created = true
                ON MATCH SET rel.remediation_batch_id = $batch, rel.remediation_updated = true
                RETURN rel.remediation_created AS created
            """, case_id=case_id, lead_id=lead_id, batch=BATCH_ID)
            rec = await res.single()
            if rec and rec["created"]: edges_created += 1
            elif rec: edges_updated += 1

    print(f"Lead Nodes: {nodes_created} created, {nodes_updated} updated")
    print(f"HAS_LEAD Edges: {edges_created} created, {edges_updated} updated")

async def project_assertions(pg, neo4j_session):
    print("Projecting Assertions...")
    rows = await pg.fetch("SELECT assertion_id, subject_entity_id, predicate, object_entity_id FROM civix.assertion")
    nodes_created, nodes_updated = 0, 0
    edges_created, edges_updated = 0, 0
    
    for r in rows:
        ass_id = str(r["assertion_id"])
        sub_id = str(r["subject_entity_id"])
        obj_id = str(r["object_entity_id"])
        pred = r["predicate"]
        props = {
            "assertion_id": ass_id,
            "name": pred,
            "predicate": pred
        }
        
        # Merge Node
        res = await neo4j_session.run("""
            MERGE (a:Assertion {assertion_id: $ass_id})
            ON CREATE SET a += $props, a.remediation_batch_id = $batch, a.remediation_created = true
            ON MATCH SET a += $props, a.remediation_batch_id = $batch, a.remediation_updated = true
            RETURN a.remediation_created AS created
        """, ass_id=ass_id, props=props, batch=BATCH_ID)
        rec = await res.single()
        if rec and rec["created"]: nodes_created += 1
        elif rec: nodes_updated += 1
        
        # Merge Sub Edge
        res = await neo4j_session.run("""
            MATCH (e {entity_id: $sub_id})
            MATCH (a:Assertion {assertion_id: $ass_id})
            MERGE (e)-[rel:ASSERTED_BY]->(a)
            ON CREATE SET rel.remediation_batch_id = $batch, rel.remediation_created = true
            ON MATCH SET rel.remediation_batch_id = $batch, rel.remediation_updated = true
            RETURN rel.remediation_created AS created
        """, sub_id=sub_id, ass_id=ass_id, batch=BATCH_ID)
        rec = await res.single()
        if rec and rec["created"]: edges_created += 1
        elif rec: edges_updated += 1
        
        # Merge Obj Edge
        res = await neo4j_session.run("""
            MATCH (a:Assertion {assertion_id: $ass_id})
            MATCH (e {entity_id: $obj_id})
            MERGE (a)-[rel:ASSERTS]->(e)
            ON CREATE SET rel.remediation_batch_id = $batch, rel.remediation_created = true
            ON MATCH SET rel.remediation_batch_id = $batch, rel.remediation_updated = true
            RETURN rel.remediation_created AS created
        """, obj_id=obj_id, ass_id=ass_id, batch=BATCH_ID)
        rec = await res.single()
        if rec and rec["created"]: edges_created += 1
        elif rec: edges_updated += 1

    print(f"Assertion Nodes: {nodes_created} created, {nodes_updated} updated")
    print(f"Assertion Edges: {edges_created} created, {edges_updated} updated")

async def main():
    pg = await asyncpg.connect(DB_URL)
    driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    
    print("=== BEGINNING PROJECTION REMEDIATION ===")
    
    async with driver.session() as neo4j_session:
        await project_events(pg, neo4j_session)
        await project_event_participants(pg, neo4j_session)
        await project_locations(pg, neo4j_session)
        await project_event_locations(pg, neo4j_session)
        await project_evidence(pg, neo4j_session)
        await project_firs(pg, neo4j_session)
        await project_leads(pg, neo4j_session)
        await project_assertions(pg, neo4j_session)

    await driver.close()
    await pg.close()
    
    print("=== PROJECTION REMEDIATION COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(main())
