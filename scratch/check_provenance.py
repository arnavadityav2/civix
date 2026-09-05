import asyncio
import json
from sqlalchemy import text
from civix_api.database import engine

async def check_hero_cases():
    async with engine.connect() as conn:
        # Load protected_hero_cases.json if it exists
        try:
            with open("database/protected_hero_cases.json", "r") as f:
                hero_manifest = json.load(f)
                hero_ids = [h["case_id"] for h in hero_manifest.get("cases", [])]
                hero_numbers = [h["case_number"] for h in hero_manifest.get("cases", [])]
                print(f"Manifest hero cases count: {len(hero_ids)}")
                print(f"Hero case numbers: {hero_numbers}")
        except Exception as e:
            print("Hero manifest load error:", e)

        # Check if case_number starting with CIV- vs SYN-
        res = await conn.execute(text("""
            SELECT 
                case_number, 
                case_id,
                CASE 
                    WHEN case_number LIKE 'CIV-%' OR case_number LIKE 'FIR-%' THEN 'GOLDEN'
                    ELSE 'SYNTHETIC'
                END as provenance
            FROM civix.investigative_case
        """))
        cases = res.fetchall()
        golden = [c for c in cases if c[2] == 'GOLDEN']
        synthetic = [c for c in cases if c[2] == 'SYNTHETIC']
        print(f"Golden count ({len(golden)}): {[c[0] for c in golden]}")
        print(f"Synthetic count ({len(synthetic)})")

if __name__ == "__main__":
    asyncio.run(check_hero_cases())
