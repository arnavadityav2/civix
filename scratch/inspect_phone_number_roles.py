import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    cid = "1346a86d-267a-a635-9d62-e34c76ecd24f"
    
    print("=== INSPECTING PHONE NUMBERS IN case_entity_role FOR CIV-2012-001 ===")
    
    roles = await conn.fetch("""
        SELECT cer.role, cer.role_basis, COUNT(*) as cnt
        FROM civix.case_entity_role cer
        JOIN civix.entity e ON cer.entity_id = e.entity_id
        WHERE cer.case_id = $1 AND e.entity_type = 'PHONE_NUMBER'
        GROUP BY cer.role, cer.role_basis
    """, cid)
    
    for r in roles:
        print(f"Role: {r['role']} | Basis: {r['role_basis']} | Count: {r['cnt']}")

    # Check sample phone number records
    sample = await conn.fetch("""
        SELECT cer.role_id, cer.entity_id, cer.role, cer.role_basis, cer.assigned_by
        FROM civix.case_entity_role cer
        JOIN civix.entity e ON cer.entity_id = e.entity_id
        WHERE cer.case_id = $1 AND e.entity_type = 'PHONE_NUMBER'
        LIMIT 10
    """, cid)
    
    print("\nSample 10 Phone Number roles:")
    for s in sample:
        print(f"  Role ID: {s['role_id']} | Entity ID: {s['entity_id']} | Role: {s['role']} | Basis: {s['role_basis']}")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
