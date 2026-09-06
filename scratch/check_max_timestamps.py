import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    
    # Check max timestamps in evidence, events, leads, cases
    max_ev = await conn.fetchval("SELECT MAX(tx_start) FROM civix.evidence_instance")
    max_event = await conn.fetchval("SELECT MAX(tx_start) FROM civix.event")
    max_lead = await conn.fetchval("SELECT MAX(created_at) FROM civix.investigative_lead")
    max_case = await conn.fetchval("SELECT MAX(updated_at) FROM civix.investigative_case")
    
    print(f"Max evidence tx_start: {max_ev}")
    print(f"Max event tx_start: {max_event}")
    print(f"Max lead created_at: {max_lead}")
    print(f"Max case updated_at: {max_case}")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
