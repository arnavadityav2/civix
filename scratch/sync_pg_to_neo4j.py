import os
import asyncio
import asyncpg
from neo4j import GraphDatabase

async def sync_pg_to_neo4j():
    db_url = os.environ.get("CIVIX_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/civix_demo")
    # Convert asyncpg driver string if needed
    db_url_clean = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    neo4j_uri = os.environ.get("NEO4J_URI", "bolt://localhost:7688")
    neo4j_user = os.environ.get("NEO4J_USER", "neo4j")
    neo4j_pass = os.environ.get("NEO4J_PASSWORD", "neo4j_demo_password_123")

    print(f"=== SYNCING POSTGRESQL DATA ({db_url_clean}) TO NEO4J ({neo4j_uri}) ===")
    pg_conn = await asyncpg.connect(db_url_clean)
    
    driver = None
    for pwd in [neo4j_pass, "password", "neo4j_demo_password_123"]:
        try:
            d = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, pwd))
            d.verify_connectivity()
            driver = d
            print(f"Connected to Neo4j successfully using password '{pwd}'")
            break
        except Exception:
            continue
            
    if not driver:
        print("Failed to authenticate to Neo4j. Skipping graph sync.")
        await pg_conn.close()
        return



    # 1. Sync Cases from civix.investigative_case
    cases = await pg_conn.fetch("""
        SELECT case_id, case_number, title, case_type, status, priority, jurisdiction 
        FROM civix.investigative_case
    """)
    print(f"Syncing {len(cases)} cases to Neo4j...")
    with driver.session() as session:
        for c in cases:
            cid = str(c['case_id'])
            cnum = c['case_number']
            title = c['title']
            ctype = c['case_type']
            prio = c['priority']
            status = c['status']
            
            session.run("""
                MERGE (c:Case {case_id: $case_id})
                SET c.case_number = $case_number,
                    c.title = $title,
                    c.case_type = $case_type,
                    c.priority = $priority,
                    c.status = $status,
                    c.visibility_status = 'ACTIVE'
            """, case_id=cid, case_number=cnum, title=title, case_type=ctype, priority=prio, status=status)

    # 2. Sync Persons
    persons = await pg_conn.fetch("""
        SELECT p.entity_id, p.display_name, p.gender, p.nationality
        FROM civix.person p
    """)
    print(f"Syncing {len(persons)} persons to Neo4j...")
    with driver.session() as session:
        for p in persons:
            eid = str(p['entity_id'])
            name = p['display_name']
            session.run("""
                MERGE (p:Person {entity_id: $entity_id})
                SET p.display_name = $name,
                    p.name = $name,
                    p.gender = $gender,
                    p.nationality = $nat,
                    p.visibility_status = 'ACTIVE'
            """, entity_id=eid, name=name, gender=p['gender'], nat=p['nationality'])

    # 3. Sync Organizations
    orgs = await pg_conn.fetch("""
        SELECT o.entity_id, o.legal_name, o.org_type
        FROM civix.organization o
    """)
    print(f"Syncing {len(orgs)} organizations to Neo4j...")
    with driver.session() as session:
        for o in orgs:
            eid = str(o['entity_id'])
            name = o['legal_name']
            session.run("""
                MERGE (o:Organization {entity_id: $entity_id})
                SET o.legal_name = $name,
                    o.display_name = $name,
                    o.name = $name,
                    o.org_type = $type,
                    o.visibility_status = 'ACTIVE'
            """, entity_id=eid, name=name, type=o['org_type'])

    # 4. Sync Vehicles
    vehicles = await pg_conn.fetch("""
        SELECT v.entity_id, v.registration_number, v.vehicle_type, v.make, v.model
        FROM civix.vehicle v
    """)
    print(f"Syncing {len(vehicles)} vehicles to Neo4j...")
    with driver.session() as session:
        for v in vehicles:
            eid = str(v['entity_id'])
            reg = v['registration_number']
            session.run("""
                MERGE (v:Vehicle {entity_id: $entity_id})
                SET v.registration_number = $reg,
                    v.display_name = $reg,
                    v.name = $reg,
                    v.vehicle_type = $vtype,
                    v.make = $make,
                    v.model = $model,
                    v.visibility_status = 'ACTIVE'
            """, entity_id=eid, reg=reg, vtype=v['vehicle_type'], make=v['make'], model=v['model'])

    # 5. Sync Phone Numbers
    phones = await pg_conn.fetch("""
        SELECT ph.entity_id, ph.msisdn
        FROM civix.phone_number ph
    """)
    print(f"Syncing {len(phones)} phone numbers to Neo4j...")
    with driver.session() as session:
        for ph in phones:
            eid = str(ph['entity_id'])
            num = ph['msisdn']
            session.run("""
                MERGE (p:PhoneNumber {entity_id: $entity_id})
                SET p.msisdn = $num,
                    p.display_name = $num,
                    p.name = $num,
                    p.visibility_status = 'ACTIVE'
            """, entity_id=eid, num=num)

    # 6. Sync Case Entity Roles (HAS_ROLE relationships)
    roles = await pg_conn.fetch("""
        SELECT role_id, case_id, entity_id, role, role_basis
        FROM civix.case_entity_role
        WHERE tx_end IS NULL
    """)
    print(f"Syncing {len(roles)} case_entity_role HAS_ROLE edges to Neo4j...")
    with driver.session() as session:
        synced_edges = 0
        for r in roles:
            rid = str(r['role_id'])
            cid = str(r['case_id'])
            eid = str(r['entity_id'])
            role_name = str(r['role'])
            basis = r['role_basis']
            
            res = session.run("""
                MATCH (c:Case {case_id: $case_id})
                MATCH (e {entity_id: $entity_id})
                MERGE (c)-[rel:HAS_ROLE {role_id: $role_id}]->(e)
                SET rel.role = $role,
                    rel.role_basis = $basis
                RETURN count(rel) AS cnt
            """, case_id=cid, entity_id=eid, role_id=rid, role=role_name, basis=basis)
            rec = res.single()
            if rec and rec['cnt'] > 0:
                synced_edges += 1
        print(f"Successfully synced {synced_edges} HAS_ROLE relationships!")

    # 7. Check graph queries for demo cases
    demo_cases = await pg_conn.fetch("SELECT case_id, case_number, title FROM civix.investigative_case ORDER BY created_at DESC LIMIT 12")
    print("\n=== VERIFYING GRAPH DATA FOR CANONICAL 12 CASES ===")
    with driver.session() as session:
        for dc in demo_cases:
            cid = str(dc['case_id'])
            cnum = dc['case_number']
            res = session.run("""
                MATCH (c:Case {case_id: $case_id})-[r:HAS_ROLE]->(e)
                RETURN c.case_number AS cnum, count(e) AS entity_count, collect(r.role) AS roles, collect(labels(e)) AS labels
            """, case_id=cid)
            rec = res.single()
            if rec:
                print(f"Case {cnum} ({cid[:8]}...): {rec['entity_count']} connected entities. Roles: {rec['roles']}")
            else:
                print(f"Case {cnum} ({cid[:8]}...): No HAS_ROLE edges found.")

    await pg_conn.close()
    driver.close()

if __name__ == '__main__':
    asyncio.run(sync_pg_to_neo4j())
