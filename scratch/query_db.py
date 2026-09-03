import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5433/civix_test')
    rows = await conn.fetch("SELECT COUNT(*) FROM civix.observation")
    print(f"Total observations: {rows[0]['count']}")
    
    # Let's search by something simpler
    rows = await conn.fetch("SELECT observation_id, observation_text FROM civix.observation")
    found_neha = False
    for r in rows:
        text = r['observation_text'].lower()
        if 'neha' in text:
            print("Found Neha in:", r['observation_text'][:100])
            found_neha = True
    if not found_neha:
        print("Neha not found at all!")
    await conn.close()

if __name__ == '__main__':
    asyncio.run(main())
