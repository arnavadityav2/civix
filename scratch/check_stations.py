import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath("."))
from sqlalchemy import text
from civix_api.database import engine

async def main():
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT DISTINCT police_station FROM civix.fir WHERE police_station IS NOT NULL"))
        stations_fir = [r[0] for r in res.fetchall()]
        print(f"FIR police stations ({len(stations_fir)}): {stations_fir}")
        
        res = await conn.execute(text("SELECT location_name FROM civix.location WHERE location_name LIKE '%Police Station%' OR location_name LIKE '%PS %'"))
        stations_loc = [r[0] for r in res.fetchall()]
        print(f"Location police stations ({len(stations_loc)}): {stations_loc}")

if __name__ == "__main__":
    asyncio.run(main())
