import psycopg
import secrets

conn = psycopg.connect("postgresql://postgres:postgres@localhost:5433/civix_test")
cur = conn.cursor()

# Find admin/supervisor users
cur.execute("SELECT user_id, username, role FROM civix.civix_user ORDER BY role LIMIT 10")
users = cur.fetchall()
print("=== Existing Users ===")
for u in users:
    print(f"  {u[2]:15s} {u[1]:30s} {u[0]}")

conn.close()

# Generate a JWT secret for dev use
jwt_secret = "civix-dev-secret-round2-do-not-use-in-production-change-this"
print(f"\n=== Recommended .env additions ===")
print(f"CIVIX_JWT_SECRET={jwt_secret}")
print(f"GEMINI_API_KEY=<your-key-here>")
