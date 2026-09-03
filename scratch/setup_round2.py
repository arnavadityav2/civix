"""
CIVIX Round 2A — Setup Script
Creates admin user, generates JWT token, and verifies the environment.
Run this ONCE before running the E2E test.
"""
import psycopg
import jwt
import uuid
from datetime import datetime, timezone, timedelta
import hashlib

DB_URL = "postgresql://postgres:postgres@localhost:5433/civix_test"
JWT_SECRET = "civix-dev-secret-round2-do-not-use-in-production-change-this"

conn = psycopg.connect(DB_URL)
cur = conn.cursor()

print("=== CIVIX Round 2A Setup ===\n")

# 1. Check if admin user exists
cur.execute("SELECT user_id, username, role FROM civix.civix_user WHERE role = 'ADMIN' LIMIT 1")
admin = cur.fetchone()

if admin:
    admin_id = admin[0]
    admin_username = admin[1]
    print(f"Admin user found: {admin_username} ({admin_id})")
else:
    # Create admin user
    admin_id = uuid.uuid4()
    admin_username = "round2_admin"
    # Hash a password (not used for JWT auth, but required by schema)
    pwd_hash = hashlib.sha256(b"round2_admin_password").hexdigest()
    cur.execute("""
        INSERT INTO civix.civix_user (user_id, username, role, clearance_level)
        VALUES (%s, %s, 'ADMIN', 5)
        ON CONFLICT (username) DO NOTHING
        RETURNING user_id
    """, (admin_id, admin_username))
    result = cur.fetchone()
    if result is None:
        # Conflict — fetch existing
        cur.execute("SELECT user_id FROM civix.civix_user WHERE username = %s", (admin_username,))
        admin_id = cur.fetchone()[0]
    conn.commit()
    print(f"Created admin user: {admin_username} ({admin_id})")

# 2. Check source unique constraint
cur.execute("SELECT indexname FROM pg_indexes WHERE tablename = 'source' AND schemaname = 'civix'")
indexes = [r[0] for r in cur.fetchall()]
print(f"\nSource table indexes: {indexes}")

# Add unique constraint on source_name if missing
cur.execute("""
    SELECT COUNT(*) FROM information_schema.table_constraints 
    WHERE table_schema='civix' AND table_name='source' 
    AND constraint_type='UNIQUE'
""")
unique_count = cur.fetchone()[0]
print(f"Source table UNIQUE constraints: {unique_count}")

if unique_count == 0:
    print("WARNING: civix.source has no UNIQUE constraint on source_name.")
    print("The ensure_nlp_source_exists() function uses ON CONFLICT (source_name) which may fail.")
    print("Will use a SELECT-then-INSERT approach instead.")
else:
    print("Source table has UNIQUE constraint — ON CONFLICT (source_name) will work.")

conn.close()

# 3. Generate JWT token for admin
payload = {
    "sub": str(admin_id),
    "exp": datetime.now(timezone.utc) + timedelta(days=30),
    "iat": datetime.now(timezone.utc),
}
token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

print(f"\n=== Admin JWT Token (valid 30 days) ===")
print(f"User ID: {admin_id}")
print(f"Username: {admin_username}")
print(f"\nBEARER TOKEN:")
print(token)

print(f"\n=== .env File Status ===")
try:
    with open(".env", "r") as f:
        content = f.read()
    print("Current .env:")
    print(content)
    
    if "CIVIX_JWT_SECRET" not in content:
        print("\n⚠️  CIVIX_JWT_SECRET missing from .env — add it.")
    if "GEMINI_API_KEY" not in content:
        print("⚠️  GEMINI_API_KEY missing from .env — add it for NLP.")
except FileNotFoundError:
    print(".env not found!")
