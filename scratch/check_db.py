import asyncio
from sqlalchemy import text
from civix_api.database import AsyncSessionLocal
import json
import httpx

async def check():
    async with AsyncSessionLocal() as session:
        q = text("SELECT entity_id, display_name, avatar_url FROM civix.person WHERE display_name = 'Suresh Valmiki'")
        r = await session.execute(q)
        print("DB Record:", r.fetchall())
        
    async with httpx.AsyncClient() as client:
        # Assuming the backend is running, let's try to fetch from it.
        # But we need auth token, which might be hard to get here. 
        pass

asyncio.run(check())
