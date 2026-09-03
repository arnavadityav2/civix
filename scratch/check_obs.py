import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5433/civix_test')
    rows = await conn.fetch("SELECT o.observation_id, o.instance_id, i.artifact_id FROM civix.observation o LEFT JOIN civix.evidence_instance i ON o.instance_id = i.instance_id WHERE o.observation_text ILIKE '%Neha Coordinator%'")
    for r in rows:
        print(f"Observation: {r['observation_id']}, Instance: {r['instance_id']}, Artifact: {r['artifact_id']}")
    await conn.close()

if __name__ == '__main__':
    asyncio.run(main())
