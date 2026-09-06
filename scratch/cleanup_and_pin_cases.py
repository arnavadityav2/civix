import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    
    test_case_numbers = ['TEST-ORDER-001', '20226-055-TEST', '20226-055', 'ACL-446c2c', 'ACL-f27e3e']
    
    async with conn.transaction():
        # Get case_ids
        rows = await conn.fetch("SELECT case_id, case_number FROM civix.investigative_case WHERE case_number = ANY($1)", test_case_numbers)
        case_ids = [r['case_id'] for r in rows]
        print(f"Found {len(case_ids)} test cases to delete: {[r['case_number'] for r in rows]}")
        
        if case_ids:
            # Delete references
            await conn.execute("DELETE FROM civix.case_access WHERE case_id = ANY($1)", case_ids)
            await conn.execute("DELETE FROM civix.case_entity_role WHERE case_id = ANY($1)", case_ids)
            await conn.execute("DELETE FROM civix.evidence_instance WHERE case_id = ANY($1)", case_ids)
            await conn.execute("DELETE FROM civix.event_location WHERE case_id = ANY($1)", case_ids)
            await conn.execute("DELETE FROM civix.investigative_lead WHERE case_id = ANY($1)", case_ids)
            await conn.execute("DELETE FROM civix.fir WHERE case_id = ANY($1)", case_ids)
            await conn.execute("DELETE FROM civix.investigative_case WHERE case_id = ANY($1)", case_ids)
            print("Successfully deleted test cases and references.")

        # Update top 3 golden cases updated_at timestamps
        # 1. CIV-2012-001 -> 2026-09-06 01:50:00+00
        # 2. CIV-2026-009 -> 2026-09-06 01:40:00+00
        # 3. CIV-2024-010 -> 2026-09-06 01:30:00+00
        
        res1 = await conn.execute("""
            UPDATE civix.investigative_case 
            SET updated_at = '2026-09-06 01:50:00+00' 
            WHERE case_number = 'CIV-2012-001'
        """)
        res2 = await conn.execute("""
            UPDATE civix.investigative_case 
            SET updated_at = '2026-09-06 01:40:00+00' 
            WHERE case_number = 'CIV-2026-009'
        """)
        res3 = await conn.execute("""
            UPDATE civix.investigative_case 
            SET updated_at = '2026-09-06 01:30:00+00' 
            WHERE case_number = 'CIV-2024-010'
        """)
        print(f"Updated timestamps for flagship golden cases: {res1}, {res2}, {res3}")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
