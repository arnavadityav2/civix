import sys
import os
sys.path.insert(0, os.path.abspath("."))
import asyncio
from scripts.hero_protection import build_hero_world_snapshot
from civix_api.database import engine

async def main():
    async with engine.connect() as conn:
        s = await build_hero_world_snapshot(conn)
        print("Snapshot overall hash:", s["overall_hash"])
        for k in s:
            if k != "overall_hash":
                print(f"  {k}: {s[k]['count']} rows, hash={s[k]['hash']}")

if __name__ == "__main__":
    asyncio.run(main())
