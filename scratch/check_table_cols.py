import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    tables = ['event', 'evidence_artifact', 'evidence_instance', 'assertion', 'investigative_lead', 'fir']
    for t in tables:
        cols = await conn.fetch(f"SELECT column_name FROM information_schema.columns WHERE table_schema='civix' AND table_name='{t}';")
        print(f"=== {t} ===")
        print([c['column_name'] for c in cols])
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
