import asyncio
import asyncpg

async def check_canonical_roles():
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    
    # 1. Fetch 12 canonical cases
    canonical_cases = await conn.fetch("""
        SELECT case_id, case_number, title
        FROM civix.investigative_case
        WHERE case_number LIKE 'CIV-%'
        ORDER BY case_number
    """)
    print(f"Total canonical CIV- cases: {len(canonical_cases)}")

    for c in canonical_cases:
        cid = c['case_id']
        cnum = c['case_number']
        title = c['title']
        roles = await conn.fetch("""
            SELECT r.role_id, r.entity_id, r.role, p.display_name AS person_name, o.legal_name AS org_name, v.registration_number AS vehicle_reg
            FROM civix.case_entity_role r
            LEFT JOIN civix.person p ON r.entity_id = p.entity_id
            LEFT JOIN civix.organization o ON r.entity_id = o.entity_id
            LEFT JOIN civix.vehicle v ON r.entity_id = v.entity_id
            WHERE r.case_id = $1 AND r.tx_end IS NULL
        """, cid)
        print(f"\nCase {cnum} ({cid}) - '{title}'")
        print(f"  Active roles count: {len(roles)}")
        for r in roles:
            name = r['person_name'] or r['org_name'] or r['vehicle_reg'] or str(r['entity_id'])
            print(f"    - Role: {r['role']} | Entity: {name} ({r['entity_id']})")

    await conn.close()

if __name__ == '__main__':
    asyncio.run(check_canonical_roles())
