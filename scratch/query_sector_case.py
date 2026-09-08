import asyncio
from civix_api.database import engine
from sqlalchemy import text

async def main():
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT case_id, case_number, title FROM civix.investigative_case WHERE case_number LIKE '%2012%' OR title ILIKE '%dwarka%'"))
        cases = res.fetchall()
        print("Dwarka / 2012 Cases:", cases)

        for c in cases:
            cid, cnum, title = c
            print(f"\n=======================================================")
            print(f"CASE: {cnum} - {title} (ID: {cid})")
            print(f"=======================================================")

            res_p = await conn.execute(text("""
                SELECT e.entity_id, p.display_name, p.avatar_url
                FROM civix.case_entity_role cer
                JOIN civix.entity e ON cer.entity_id = e.entity_id
                LEFT JOIN civix.person p ON e.entity_id = p.entity_id
                WHERE cer.case_id = :cid AND e.entity_type = 'PERSON'
            """), {"cid": cid})
            persons = res_p.fetchall()
            print(f"Total Persons linked in DB: {len(persons)}")
            for p in persons:
                print(f"  DB Person: {p[1]} | Avatar: {p[2]}")

        # Also check frontend hardcoded / mock person list for CIV-2012-001 in CaseWorkspacePage / BiometricIntelligencePage!
        print("\nChecking mock frontend cases in cases.ts or BiometricIntelligencePage.tsx / CaseWorkspacePage.tsx...")

if __name__ == '__main__':
    asyncio.run(main())
