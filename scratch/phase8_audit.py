#!/usr/bin/env python3
"""
Phase 8: Full System Validation & Investigative Experience Audit
Read-Only Data Collection Script
"""
import asyncio
import sys
import os
import json
import httpx
from sqlalchemy import text
from neo4j import GraphDatabase

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from civix_api.database import engine
from civix_api.config import settings
from scripts.hero_protection import build_hero_world_snapshot, get_protected_hero_case_ids

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def run_db_audit():
    print("=========================================")
    print("1. RUNTIME & DB HEALTH")
    print("=========================================")
    try:
        async with engine.connect() as conn:
            r = await conn.execute(text("SELECT version();"))
            print(f"PostgreSQL: {r.scalar()}")
    except Exception as e:
        print(f"PostgreSQL Error: {e}")

    try:
        neo4j_driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
        with neo4j_driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) AS node_count")
            node_count = result.single()["node_count"]
            print(f"Neo4j Reachable: YES, Total Nodes: {node_count}")
    except Exception as e:
        print(f"Neo4j Error: {e}")

    print("\n=========================================")
    print("2. HERO WORLD REGRESSION TEST")
    print("=========================================")
    try:
        async with engine.connect() as conn:
            hero_snapshot = await build_hero_world_snapshot(conn)
            hero_ids = get_protected_hero_case_ids()
            
            baseline_hash = "e520f5a618dc553b4d0b7cfb2579b5e37a56eb3e0c220d75b7677a5d7816369e"
            current_hash = hero_snapshot['overall_hash']
            print(f"Hero Count: {len(hero_ids)}")
            print(f"Baseline Hash: {baseline_hash}")
            print(f"Current Hash:  {current_hash}")
            if current_hash == baseline_hash:
                print("Result: MATCH")
            else:
                print("Result: P0 CRITICAL MISMATCH")
    except Exception as e:
        print(f"Hero Snapshot Error: {e}")

    print("\n=========================================")
    print("3. SYNTHETIC WORLD VALIDATION")
    print("=========================================")
    try:
        async with engine.connect() as conn:
            # Case counts
            r = await conn.execute(text("SELECT COUNT(*) FROM civix.investigative_case;"))
            total_cases = r.scalar()
            r = await conn.execute(text("SELECT COUNT(*) FROM civix.investigative_case WHERE case_number LIKE 'SYN-%';"))
            syn_cases = r.scalar()
            
            print(f"Total Cases: {total_cases}")
            print(f"Hero Cases: {total_cases - syn_cases}")
            print(f"Synthetic Cases: {syn_cases}")
            
            # Events
            r = await conn.execute(text("SELECT COUNT(*) FROM civix.event e JOIN civix.event_location el ON e.event_id = el.event_id JOIN civix.investigative_case c ON el.case_id = c.case_id WHERE c.case_number LIKE 'SYN-%';"))
            syn_events = r.scalar()
            print(f"\nSynthetic Events: {syn_events}")
            
            r = await conn.execute(text("""
                SELECT MIN(cnt), MAX(cnt), AVG(cnt), PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY cnt) 
                FROM (
                    SELECT el.case_id, COUNT(*) as cnt 
                    FROM civix.event_location el 
                    JOIN civix.investigative_case c ON el.case_id = c.case_id 
                    WHERE c.case_number LIKE 'SYN-%' 
                    GROUP BY el.case_id
                ) t;
            """))
            ev_min, ev_max, ev_avg, ev_med = r.fetchone()
            print(f"Events/Case - Min: {ev_min}, Max: {ev_max}, Avg: {ev_avg:.2f}, Median: {ev_med}")
            
            # Event Locations
            r = await conn.execute(text("""
                SELECT 
                    SUM(CASE WHEN distinct_locs = 1 THEN 1 ELSE 0 END) as count_1,
                    SUM(CASE WHEN distinct_locs >= 2 THEN 1 ELSE 0 END) as count_2plus,
                    SUM(CASE WHEN distinct_locs >= 3 THEN 1 ELSE 0 END) as count_3plus,
                    SUM(CASE WHEN distinct_locs >= 4 THEN 1 ELSE 0 END) as count_4plus,
                    AVG(distinct_locs) as avg_locs
                FROM (
                    SELECT el.case_id, COUNT(DISTINCT el.location_id) as distinct_locs
                    FROM civix.event_location el
                    JOIN civix.investigative_case c ON el.case_id = c.case_id
                    WHERE c.case_number LIKE 'SYN-%'
                    GROUP BY el.case_id
                ) t;
            """))
            c1, c2, c3, c4, avg_locs = r.fetchone()
            print(f"\nSynthetic Cases with 1 Location: {c1}")
            print(f"Synthetic Cases with >=2 Locations: {c2}")
            print(f"Synthetic Cases with >=3 Locations: {c3}")
            print(f"Synthetic Cases with >=4 Locations: {c4}")
            print(f"Avg Distinct Locations / Synthetic Case: {avg_locs:.2f}")

            # Leads
            r = await conn.execute(text("SELECT COUNT(*) FROM civix.investigative_lead l JOIN civix.investigative_case c ON l.case_id = c.case_id WHERE c.case_number LIKE 'SYN-%';"))
            total_syn_leads = r.scalar()
            
            r = await conn.execute(text("""
                SELECT 
                    SUM(CASE WHEN cnt = 0 THEN 1 ELSE 0 END) as c0,
                    SUM(CASE WHEN cnt = 1 THEN 1 ELSE 0 END) as c1,
                    SUM(CASE WHEN cnt = 2 THEN 1 ELSE 0 END) as c2,
                    SUM(CASE WHEN cnt >= 3 THEN 1 ELSE 0 END) as c3plus
                FROM (
                    SELECT c.case_id, COUNT(l.lead_id) as cnt
                    FROM civix.investigative_case c
                    LEFT JOIN civix.investigative_lead l ON c.case_id = l.case_id
                    WHERE c.case_number LIKE 'SYN-%'
                    GROUP BY c.case_id
                ) t;
            """))
            l0, l1, l2, l3 = r.fetchone()
            print(f"\nTotal Synthetic Leads: {total_syn_leads}")
            print(f"Synthetic Cases with 0 leads: {l0}")
            print(f"Synthetic Cases with 1 lead: {l1}")
            print(f"Synthetic Cases with 2 leads: {l2}")
            print(f"Synthetic Cases with 3+ leads: {l3}")
            print(f"Avg Leads / Synthetic Case: {total_syn_leads / syn_cases if syn_cases > 0 else 0:.2f}")

            # Descriptions
            r = await conn.execute(text("""
                SELECT 
                    SUM(CASE WHEN e.description LIKE 'Event #%' OR e.description IS NULL THEN 1 ELSE 0 END) as generic,
                    SUM(CASE WHEN e.description NOT LIKE 'Event #%' AND e.description IS NOT NULL THEN 1 ELSE 0 END) as enriched
                FROM civix.event e
                JOIN civix.event_location el ON e.event_id = el.event_id
                JOIN civix.investigative_case c ON el.case_id = c.case_id
                WHERE c.case_number LIKE 'SYN-%';
            """))
            generic, enriched = r.fetchone()
            print(f"\nGeneric Descriptions: {generic}")
            print(f"Enriched Descriptions: {enriched}")
            print(f"Percentage Enriched: {enriched / (generic + enriched) * 100 if (generic + enriched) > 0 else 0:.2f}%")

    except Exception as e:
        print(f"Synthetic Audit Error: {e}")

    print("\n=========================================")
    print("4. GRAPH & ENTITY VALIDATION")
    print("=========================================")
    try:
        async with engine.connect() as conn:
            # Check Neo4j relationships vs PG
            with neo4j_driver.session() as session:
                res = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
                rel_count = res.single()["rel_count"]
                print(f"Neo4j Total Relationships: {rel_count}")
                
                res = session.run("MATCH (c:InvestigativeCase) RETURN count(c) as case_count")
                print(f"Neo4j Case Nodes: {res.single()['case_count']}")
                
                res = session.run("MATCH (e:Entity) RETURN count(e) as entity_count")
                print(f"Neo4j Entity Nodes: {res.single()['entity_count']}")
    except Exception as e:
        print(f"Graph Audit Error: {e}")

    print("\n=========================================")
    print("5. API ENDPOINT SMOKE TESTS")
    print("=========================================")
    import jwt
    import time
    
    # Get a valid user to create a token for
    valid_user_id = None
    try:
        async with engine.connect() as conn:
            r = await conn.execute(text("SELECT user_id FROM civix.civix_user LIMIT 1"))
            row = r.fetchone()
            if row:
                valid_user_id = str(row[0])
    except Exception as e:
        pass
        
    if not valid_user_id:
        print("Could not find a valid user in civix.civix_user for API testing.")
        return

    # Generate token
    token = jwt.encode(
        {"sub": valid_user_id, "exp": int(time.time()) + 3600},
        settings.civix_jwt_secret,
        algorithm="HS256"
    )
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(base_url="http://localhost:8000", headers=headers) as client:
        try:
            # Test cases endpoint
            resp = await client.get("/api/v1/cases?limit=5")
            print(f"GET /api/v1/cases -> Status: {resp.status_code}")
            
            # Pick a case ID (try SYN-2025-002)
            syn_2025_002_id = None
            async with engine.connect() as conn:
                r = await conn.execute(text("SELECT case_id FROM civix.investigative_case WHERE case_number = 'SYN-2025-002'"))
                row = r.fetchone()
                if row:
                    syn_2025_002_id = row[0]
            
            if syn_2025_002_id:
                print(f"\nTesting API for case SYN-2025-002 ({syn_2025_002_id})")
                
                # Test Events / Movement
                resp = await client.get(f"/api/v1/spatial/cases/{syn_2025_002_id}/events")
                print(f"GET /api/v1/spatial/cases/{{id}}/events -> Status: {resp.status_code}")
                if resp.status_code == 200:
                    events = resp.json()
                    print(f"  Events returned: {len(events)}")
                    
                # Test Leads
                resp = await client.get(f"/api/v1/cases/{syn_2025_002_id}/leads")
                print(f"GET /api/v1/cases/{{id}}/leads -> Status: {resp.status_code}")
                if resp.status_code == 200:
                    leads = resp.json()
                    print(f"  Leads returned: {len(leads)}")
                    if len(leads) > 0:
                        print(f"  Sample Lead text: {leads[0].get('lead_text')[:60]}...")
            else:
                print("Could not find SYN-2025-002 in DB.")
        except Exception as e:
            print(f"API Audit Error: {e}")

if __name__ == "__main__":
    asyncio.run(run_db_audit())
