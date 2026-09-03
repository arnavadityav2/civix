import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5433/civix_test')
    rows = await conn.fetch("SELECT observation_id, instance_id, observation_text FROM civix.observation")
    for r in rows:
        if 'Rahul' in r['observation_text'] or 'cartel' in r['observation_text'].lower() or 'drug' in r['observation_text'].lower():
            print("FOUND NEGATIVE CANDIDATE:")
            print(r['observation_id'])
            print(r['observation_text'])
            print("---")
    await conn.close()

if __name__ == '__main__':
    asyncio.run(main())
