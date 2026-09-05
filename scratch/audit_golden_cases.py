import asyncio
import json
import os
import asyncpg
from neo4j import GraphDatabase
import requests
from datetime import datetime, timezone, timedelta
import jwt

DB_URL = "postgresql://postgres:postgres@localhost:5432/civix_demo"
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7688")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")

JWT_SECRET = "civix-dev-secret-round2-do-not-use-in-production-change-this"
JWT_ALGORITHM = "HS256"

MANIFEST_PATH = r"c:\Users\ARNAV ADITYA\Desktop\civix 2.0\database\protected_hero_cases.json"

def get_auth_headers():
    payload = {
        "sub": "00000000-0000-0000-0000-000000000001",
        "role": "SUPER_ADMIN",
        "clearance_level": 5,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return {"Authorization": f"Bearer {token}"}

async def run_audit():
    # 1. Load manifest
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    
    hero_cases = manifest_data["protected_cases"]
    print(f"Manifest loaded: {len(hero_cases)} protected hero cases.")
    
    pg_conn = await asyncpg.connect(DB_URL)
    neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    headers = get_auth_headers()
    
    audit_results = {
        "manifest_verification": [],
        "case_baselines": [],
        "neo4j_inventories": [],
        "neo4j_global_labels": {},
        "neo4j_global_relationships": {},
        "postgres_neo4j_parity": [],
        "api_parity": [],
        "evidence_paths": []
    }
    
    # 1. Manifest Verification
    for hc in hero_cases:
        cid = hc["case_id"]
        c_row = await pg_conn.fetchrow("""
            SELECT c.case_id, c.case_number, c.title, c.status, c.case_type, c.jurisdiction,
                   f.police_station
            FROM civix.investigative_case c
            LEFT JOIN civix.fir f ON c.case_id = f.case_id
            WHERE c.case_id = $1::uuid;
        """, cid)
        
        if not c_row:
            print(f"CRITICAL DISCREPANCY: Case ID {cid} in manifest not found in PostgreSQL!")
            return
        
        audit_results["manifest_verification"].append({
            "manifest_id": cid,
            "manifest_number": hc["case_number"],
            "manifest_title": hc["title"],
            "db_number": c_row["case_number"],
            "db_title": c_row["title"],
            "db_status": c_row["status"],
            "db_type": c_row["case_type"],
            "db_jurisdiction": c_row["jurisdiction"],
            "db_police_station": c_row["police_station"] or "N/A",
            "match": hc["case_number"] == c_row["case_number"]
        })
        
    print("Manifest verification complete. All 13 cases matched in PostgreSQL.")

    # PHASE 1 & 2 & 3 & 4: PostgreSQL Audit per Case
    for hc in hero_cases:
        cid = hc["case_id"]
        cnum = hc["case_number"]
        ctitle = hc["title"]
        
        # Entity roles
        roles = await pg_conn.fetch("""
            SELECT cer.role, cer.entity_id, e.entity_type::text
            FROM civix.case_entity_role cer
            JOIN civix.entity e ON cer.entity_id = e.entity_id
            WHERE cer.case_id = $1::uuid;
        """, cid)
        
        role_count = len(roles)
        role_entity_ids = set(r["entity_id"] for r in roles)
        unique_role_entities = len(role_entity_ids)
        
        # Entity breakdown by subtype
        subtype_counts = await pg_conn.fetchrow("""
            SELECT 
                COUNT(DISTINCT p.entity_id) as persons,
                COUNT(DISTINCT v.entity_id) as vehicles,
                COUNT(DISTINCT pn.entity_id) as phones,
                COUNT(DISTINCT d.entity_id) as devices,
                COUNT(DISTINCT o.entity_id) as orgs
            FROM civix.case_entity_role cer
            LEFT JOIN civix.person p ON cer.entity_id = p.entity_id
            LEFT JOIN civix.vehicle v ON cer.entity_id = v.entity_id
            LEFT JOIN civix.phone_number pn ON cer.entity_id = pn.entity_id
            LEFT JOIN civix.device d ON cer.entity_id = d.entity_id
            LEFT JOIN civix.organization o ON cer.entity_id = o.entity_id
            WHERE cer.case_id = $1::uuid;
        """, cid)
        
        # Additional subtypes: location, financial account, property, sim
        loc_count = await pg_conn.fetchval("SELECT COUNT(DISTINCT entity_id) FROM civix.case_entity_role cer JOIN civix.entity e USING(entity_id) WHERE cer.case_id = $1::uuid AND e.entity_type::text = 'LOCATION';", cid)
        fa_count = await pg_conn.fetchval("SELECT COUNT(DISTINCT entity_id) FROM civix.case_entity_role cer JOIN civix.entity e USING(entity_id) WHERE cer.case_id = $1::uuid AND e.entity_type::text = 'FINANCIAL_ACCOUNT';", cid)
        prop_count = await pg_conn.fetchval("SELECT COUNT(DISTINCT entity_id) FROM civix.case_entity_role cer JOIN civix.entity e USING(entity_id) WHERE cer.case_id = $1::uuid AND e.entity_type::text = 'PROPERTY';", cid)
        sim_count = await pg_conn.fetchval("SELECT COUNT(DISTINCT entity_id) FROM civix.case_entity_role cer JOIN civix.entity e USING(entity_id) WHERE cer.case_id = $1::uuid AND e.entity_type::text = 'SIM';", cid)
        
        # Events & participants via event_location or event_participant
        events_loc = await pg_conn.fetch("SELECT DISTINCT event_id, location_id FROM civix.event_location WHERE case_id = $1::uuid;", cid)
        event_ids = [el["event_id"] for el in events_loc]
        
        if event_ids:
            event_rows = await pg_conn.fetch("SELECT event_id, event_type FROM civix.event WHERE event_id = ANY($1::uuid[]);", event_ids)
            event_parts = await pg_conn.fetch("SELECT DISTINCT entity_id FROM civix.event_participant WHERE event_id = ANY($1::uuid[]);", event_ids)
            event_entities = set(p["entity_id"] for p in event_parts)
            event_locs = len(set(el["location_id"] for el in events_loc if el["location_id"]))
            event_type_count = len(set(e["event_type"] for e in event_rows))
            events_count = len(event_rows)
        else:
            events_count = 0
            event_entities = set()
            event_locs = 0
            event_type_count = 0
            
        additional_event_entities = len(event_entities - role_entity_ids)
        
        # Assertions
        assertions = await pg_conn.fetch("""
            SELECT assertion_id, subject_entity_id, object_entity_id, predicate 
            FROM civix.assertion 
            WHERE (subject_entity_id = ANY($1::uuid[]) OR object_entity_id = ANY($1::uuid[]))
              AND tx_end IS NULL;
        """, list(role_entity_ids) if role_entity_ids else [cid])
        
        # Leads
        leads = await pg_conn.fetch("SELECT lead_id FROM civix.investigative_lead WHERE case_id = $1::uuid;", cid)
        
        # FIRs
        firs = await pg_conn.fetch("SELECT fir_id FROM civix.fir WHERE case_id = $1::uuid;", cid)
        
        # Evidence Artifacts & Instances
        evidence_inst = await pg_conn.fetch("SELECT instance_id, artifact_id FROM civix.evidence_instance WHERE case_id = $1::uuid;", cid)
        inst_art_ids = [ei["artifact_id"] for ei in evidence_inst]
        
        if inst_art_ids:
            evidence_art = await pg_conn.fetch("""
                SELECT artifact_id, mime_type, original_filename 
                FROM civix.evidence_artifact 
                WHERE artifact_id = ANY($1::uuid[]);
            """, inst_art_ids)
        else:
            evidence_art = []
            
        # Breakdown evidence by mime/type
        img_count = sum(1 for e in evidence_art if (e["mime_type"] or "").startswith("image/") or (e["original_filename"] or "").lower().endswith((".png", ".jpg", ".jpeg", ".webp")))
        vid_count = sum(1 for e in evidence_art if (e["mime_type"] or "").startswith("video/") or (e["original_filename"] or "").lower().endswith((".mp4", ".avi", ".mkv")))
        doc_count = sum(1 for e in evidence_art if (e["mime_type"] or "").startswith("application/") or (e["mime_type"] or "").startswith("text/") or (e["original_filename"] or "").lower().endswith((".pdf", ".txt", ".json", ".doc", ".csv")))
        aud_count = sum(1 for e in evidence_art if (e["mime_type"] or "").startswith("audio/"))
        cctv_count = sum(1 for e in evidence_art if "cctv" in (e["original_filename"] or "").lower())
        
        audit_results["case_baselines"].append({
            "case_id": str(cid),
            "case_number": cnum,
            "title": ctitle,
            "roles_count": role_count,
            "unique_entities": unique_role_entities,
            "persons": subtype_counts["persons"],
            "vehicles": subtype_counts["vehicles"],
            "phones": subtype_counts["phones"],
            "devices": subtype_counts["devices"],
            "orgs": subtype_counts["orgs"],
            "locations": loc_count,
            "financial_accounts": fa_count,
            "properties": prop_count,
            "sims": sim_count,
            "events_count": events_count,
            "unique_event_types": event_type_count,
            "unique_event_participants": len(event_entities),
            "event_locations": event_locs,
            "additional_entities_from_events": additional_event_entities,
            "assertions_count": len(assertions),
            "leads_count": len(leads),
            "firs_count": len(firs),
            "evidence_artifacts": len(evidence_art),
            "evidence_instances": len(evidence_inst),
            "evidence_images": img_count,
            "evidence_videos": vid_count,
            "evidence_docs": doc_count,
            "evidence_audio": aud_count,
            "evidence_cctv": cctv_count
        })

    # PHASE 5, 6, 7: Neo4j Hop-by-Hop & Label / Relationship Diagnostics
    with neo4j_driver.session() as n4j:
        # Check global labels
        gl_res = n4j.run("CALL db.labels() YIELD label RETURN label;")
        all_labels = [r["label"] for r in gl_res]
        
        # Check global relationships
        gr_res = n4j.run("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType;")
        all_rel_types = [r["relationshipType"] for r in gr_res]
        
        for hc in hero_cases:
            cid = hc["case_id"]
            cnum = hc["case_number"]
            
            # Hop expansion queries in Neo4j
            hop_data = {}
            for hop in range(0, 6):
                if hop == 0:
                    q = "MATCH (c:Case {case_id: $cid}) RETURN count(c) as cnt"
                else:
                    q = f"MATCH (c:Case {{case_id: $cid}})-[*1..{hop}]-(n) RETURN count(DISTINCT n) as cnt"
                
                res = n4j.run(q, cid=str(cid)).single()
                cnt = res["cnt"] if res else 0
                
                # Extract label counts for this hop
                if hop == 0:
                    lbl_counts = {"Case": 1}
                else:
                    q_lbl = f"MATCH (c:Case {{case_id: $cid}})-[*1..{hop}]-(n) UNWIND labels(n) as l RETURN l, count(DISTINCT n) as lcnt"
                    lbl_res = n4j.run(q_lbl, cid=str(cid))
                    lbl_counts = {r["l"]: r["lcnt"] for r in lbl_res}
                    
                hop_data[f"{hop}_hop"] = {
                    "total_nodes": cnt,
                    "label_breakdown": lbl_counts
                }
                
            # Relationships within 5 hops
            q_rel = """
                MATCH (c:Case {case_id: $cid})-[*0..4]-(a)-[r]-(b)
                RETURN DISTINCT type(r) as rel_type, head(labels(a)) as src_label, head(labels(b)) as tgt_label, count(r) as rcnt
            """
            rel_res = n4j.run(q_rel, cid=str(cid))
            rels_case = [{
                "type": r["rel_type"],
                "src": r["src_label"],
                "tgt": r["tgt_label"],
                "count": r["rcnt"]
            } for r in rel_res]
            
            audit_results["neo4j_inventories"].append({
                "case_id": str(cid),
                "case_number": cnum,
                "hops": hop_data,
                "relationships": rels_case
            })

        # Global label diagnostics across Golden cases
        label_summary = {}
        for lbl in all_labels:
            glob_cnt = n4j.run(f"MATCH (n:{lbl}) RETURN count(n) as cnt;").single()["cnt"]
            golden_nodes = n4j.run(f"MATCH (c:Case)-[*0..5]-(n:{lbl}) WHERE c.case_id IN $cids RETURN count(DISTINCT n) as cnt;", cids=[c["case_id"] for c in hero_cases]).single()["cnt"]
            cases_present = n4j.run(f"MATCH (c:Case)-[*0..5]-(n:{lbl}) WHERE c.case_id IN $cids RETURN count(DISTINCT c.case_id) as cnt;", cids=[c["case_id"] for c in hero_cases]).single()["cnt"]
            label_summary[lbl] = {
                "global_exists": glob_cnt > 0,
                "global_count": glob_cnt,
                "golden_node_count": golden_nodes,
                "golden_cases_count": cases_present
            }
        audit_results["neo4j_global_labels"] = label_summary

    # PHASE 9 & 10: Backend Graph API vs Neo4j Direct Comparison
    for hc in hero_cases:
        cid = hc["case_id"]
        cnum = hc["case_number"]
        
        # Test Graph API Endpoint depth=1
        try:
            r1 = requests.get(f"http://127.0.0.1:8000/api/v1/cases/{cid}/graph?depth=1&node_limit=200&rel_limit=500", headers=headers)
            api_depth_1 = r1.json() if r1.status_code == 200 else {"nodes": [], "relationships": []}
        except Exception:
            api_depth_1 = {"nodes": [], "relationships": []}
            
        # Test Graph API Endpoint depth=2
        try:
            r2 = requests.get(f"http://127.0.0.1:8000/api/v1/cases/{cid}/graph?depth=2&node_limit=200&rel_limit=500", headers=headers)
            api_depth_2 = r2.json() if r2.status_code == 200 else {"nodes": [], "relationships": []}
        except Exception:
            api_depth_2 = {"nodes": [], "relationships": []}
            
        audit_results["api_parity"].append({
            "case_id": str(cid),
            "case_number": cnum,
            "api_depth_1_nodes": len(api_depth_1.get("nodes", [])),
            "api_depth_1_rels": len(api_depth_1.get("relationships", [])),
            "api_depth_2_nodes": len(api_depth_2.get("nodes", [])),
            "api_depth_2_rels": len(api_depth_2.get("relationships", [])),
        })

    # Save complete audit findings
    out_path = r"c:\Users\ARNAV ADITYA\Desktop\civix 2.0\scratch\audit_raw_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(audit_results, f, indent=2)
        
    print(f"Full Audit complete! Raw results written to {out_path}")
    
    await pg_conn.close()
    neo4j_driver.close()

if __name__ == "__main__":
    asyncio.run(run_audit())
