import asyncio
import asyncpg

async def check_manifest_linkage():
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    
    # 1. Total manifest count
    manifest_cnt = await conn.fetchval("SELECT count(*) FROM civix.evidence_generation_manifest")
    print(f"Total rows in civix.evidence_generation_manifest: {manifest_cnt}")

    # 2. Check how many manifest rows have a matching artifact_id in civix.evidence_artifact
    matched_cnt = await conn.fetchval("""
        SELECT count(*)
        FROM civix.evidence_generation_manifest m
        JOIN civix.evidence_artifact a ON m.artifact_id = a.artifact_id
    """)
    print(f"Manifest rows with matching artifact_id in evidence_artifact: {matched_cnt}")

    # 3. Check evidence_artifact records by sha256_hash status
    sample_artifacts = await conn.fetch("""
        SELECT artifact_id, storage_uri, sha256_hash, file_size_bytes
        FROM civix.evidence_artifact
        WHERE mime_type LIKE 'image/%'
        LIMIT 10
    """)
    print("\nSample 10 image evidence artifacts in DB:")
    for a in sample_artifacts:
        aid = a['artifact_id']
        uri = a['storage_uri']
        hash_hex = a['sha256_hash'].hex() if isinstance(a['sha256_hash'], bytes) else str(a['sha256_hash'])
        size = a['file_size_bytes']
        print(f"  Artifact {aid} | URI: {uri} | Size: {size} | Hash: {hash_hex[:16]}...")

    await conn.close()

if __name__ == '__main__':
    asyncio.run(check_manifest_linkage())
