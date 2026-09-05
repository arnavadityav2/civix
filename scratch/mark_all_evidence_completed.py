import asyncio
import asyncpg

async def mark_completed():
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    
    # Update processing_status to COMPLETED for all 180 image artifacts
    updated = await conn.execute("""
        UPDATE civix.evidence_artifact
        SET processing_status = 'COMPLETED',
            is_integrity_verified = true,
            processed_at = NOW()
        WHERE mime_type LIKE 'image/%'
    """)
    print(f"Updated evidence_artifact records: {updated}")

    # Check status summary
    res = await conn.fetch("""
        SELECT processing_status, count(*) 
        FROM civix.evidence_artifact 
        WHERE mime_type LIKE 'image/%' 
        GROUP BY processing_status
    """)
    print("\nImage Evidence Status Summary in DB:")
    for r in res:
        print(f"  Status: {r['processing_status']} -> Count: {r['count']}")

    await conn.close()

if __name__ == '__main__':
    asyncio.run(mark_completed())
