import asyncio
import asyncpg

async def count_persons():
    conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/civix_demo')
    
    # 1. Total unique persons across entire DB
    total_persons_db = await conn.fetchval("SELECT COUNT(*) FROM civix.person")
    
    # 2. Total unique persons linked to Golden 13 cases via case_entity_role
    golden_persons_unique = await conn.fetchval("""
        SELECT COUNT(DISTINCT cer.entity_id)
        FROM civix.case_entity_role cer
        JOIN civix.investigative_case c ON c.case_id = cer.case_id
        JOIN civix.entity e ON e.entity_id = cer.entity_id
        WHERE c.case_number NOT LIKE 'SYN-%'
          AND e.entity_type = 'PERSON';
    """)

    # 3. Total person-case roles (person links) across Golden 13 cases
    golden_person_roles_total = await conn.fetchval("""
        SELECT COUNT(*)
        FROM civix.case_entity_role cer
        JOIN civix.investigative_case c ON c.case_id = cer.case_id
        JOIN civix.entity e ON e.entity_id = cer.entity_id
        WHERE c.case_number NOT LIKE 'SYN-%'
          AND e.entity_type = 'PERSON';
    """)

    # 4. Breakdown per Golden Case
    case_breakdown = await conn.fetch("""
        SELECT c.case_number, c.title, COUNT(DISTINCT cer.entity_id) as person_count
        FROM civix.investigative_case c
        LEFT JOIN civix.case_entity_role cer ON cer.case_id = c.case_id
        LEFT JOIN civix.entity e ON e.entity_id = cer.entity_id AND e.entity_type = 'PERSON'
        WHERE c.case_number NOT LIKE 'SYN-%'
        GROUP BY c.case_id, c.case_number, c.title
        ORDER BY c.case_number;
    """)

    # 5. Role distribution among persons in Golden cases
    role_dist = await conn.fetch("""
        SELECT cer.role, COUNT(*) as count
        FROM civix.case_entity_role cer
        JOIN civix.investigative_case c ON c.case_id = cer.case_id
        JOIN civix.entity e ON e.entity_id = cer.entity_id
        WHERE c.case_number NOT LIKE 'SYN-%'
          AND e.entity_type = 'PERSON'
        GROUP BY cer.role
        ORDER BY count DESC;
    """)

    print(f"Total Person Entities in entire DB: {total_persons_db}")
    print(f"Unique Persons linked to Golden 13 Cases: {golden_persons_unique}")
    print(f"Total Person-Case Role Assignments in Golden 13 Cases: {golden_person_roles_total}\n")
    
    print("=== Breakdown by Golden Case ===")
    for row in case_breakdown:
        print(f"  {row['case_number']} | {row['person_count']} persons | {row['title']}")
        
    print("\n=== Person Role Breakdown in Golden Cases ===")
    for r in role_dist:
        print(f"  {r['role']}: {r['count']}")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(count_persons())
