import asyncio
import asyncpg
import uuid

async def check():
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5433/civix_test")
    
    case_id = uuid.UUID('b281ad86-1b43-458c-b751-fc44cb467823')
    dummy_case_id = uuid.UUID('efb6b04c-3655-4a1c-9d59-93573eb45708')
    try:
        await conn.execute("UPDATE civix.investigative_lead SET case_id = $2 WHERE case_id = $1", case_id, dummy_case_id)
        print("Moved leads to dummy case successfully!")
    except Exception as e:
        print(f"Error: {e}")
        
    await conn.close()

if __name__ == '__main__':
    asyncio.run(check())
