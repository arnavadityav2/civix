"""Check full Round 2 and Round 1 state."""
import psycopg2
import os, sys

conn = psycopg2.connect(
    host='localhost', dbname='civix_test',
    user='civix_api', password='cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx', port=5433
)
print("Connected OK to civix_test:5433")
cur = conn.cursor()

print("\n=== evidence_artifact row count ===")
cur.execute("SELECT COUNT(*) FROM civix.evidence_artifact")
print(f"  {cur.fetchone()[0]} rows")

print("\n=== evidence_artifact processing statuses ===")
try:
    cur.execute("SELECT processing_status, COUNT(*) FROM civix.evidence_artifact GROUP BY processing_status")
    for r in cur.fetchall():
        print(f"  {r}")
except Exception as e:
    print(f"  Error: {e}")
    conn.rollback()

print("\n=== outbox_event rows ===")
try:
    cur.execute("SELECT COUNT(*) FROM civix.outbox_event")
    print(f"  {cur.fetchone()[0]} rows")
    cur.execute("SELECT event_type, COUNT(*) FROM civix.outbox_event GROUP BY event_type ORDER BY event_type")
    for r in cur.fetchall():
        print(f"  {r}")
except Exception as e:
    print(f"  Error: {e}")
    conn.rollback()

print("\n=== source rows ===")
try:
    cur.execute("SELECT source_name, agency_type FROM civix.source ORDER BY source_name")
    for r in cur.fetchall():
        print(f"  {r}")
except Exception as e:
    print(f"  Error: {e}")
    conn.rollback()

print("\n=== investigative_case rows ===")
try:
    cur.execute("SELECT COUNT(*) FROM civix.investigative_case")
    print(f"  {cur.fetchone()[0]} rows")
except Exception as e:
    print(f"  Error: {e}")
    conn.rollback()

print("\n=== entity rows ===")
try:
    cur.execute("SELECT entity_type, COUNT(*) FROM civix.entity GROUP BY entity_type ORDER BY entity_type")
    for r in cur.fetchall():
        print(f"  {r}")
except Exception as e:
    print(f"  Error: {e}")
    conn.rollback()

print("\n=== assertion rows ===")
try:
    cur.execute("SELECT COUNT(*) FROM civix.assertion")
    print(f"  {cur.fetchone()[0]} rows")
except Exception as e:
    print(f"  Error: {e}")
    conn.rollback()

print("\n=== Round 1 invariant: analysis_run table ===")
try:
    cur.execute("SELECT COUNT(*) FROM civix.analysis_run")
    print(f"  analysis_run: {cur.fetchone()[0]} rows")
except Exception as e:
    print(f"  Error: {e}")
    conn.rollback()

print("\n=== Round 1 invariant: provenance table ===")
try:
    cur.execute("SELECT COUNT(*) FROM civix.provenance")
    print(f"  provenance: {cur.fetchone()[0]} rows")
except Exception as e:
    print(f"  Error: {e}")
    conn.rollback()

print("\n=== evidence_instance rows ===")
try:
    cur.execute("SELECT COUNT(*) FROM civix.evidence_instance")
    print(f"  {cur.fetchone()[0]} rows")
except Exception as e:
    print(f"  Error: {e}")
    conn.rollback()

print("\n=== observation rows ===")
try:
    cur.execute("SELECT COUNT(*) FROM civix.observation")
    print(f"  {cur.fetchone()[0]} rows")
except Exception as e:
    print(f"  Error: {e}")
    conn.rollback()

print("\n=== civix_api dir: processors ===")
for fname in os.listdir("civix_api/services/processors"):
    print(f"  {fname}")

print("\n=== GEMINI_API_KEY ===")
key = os.environ.get("GEMINI_API_KEY", "")
if key:
    print(f"  SET (length={len(key)})")
else:
    # Check .env directly
    try:
        with open(".env") as f:
            for line in f:
                if "GEMINI_API_KEY" in line:
                    val = line.split("=",1)[-1].strip()
                    if val:
                        print(f"  SET in .env (length={len(val)})")
                    else:
                        print("  EMPTY in .env — NOT SET")
    except Exception:
        print("  NOT SET")

print("\n=== PyMuPDF ===")
try:
    import fitz
    print(f"  fitz version: {fitz.version}")
except ImportError as e:
    print(f"  NOT installed: {e}")

print("\n=== google-genai ===")
try:
    from google import genai
    print("  google-genai INSTALLED")
except ImportError as e:
    print(f"  NOT installed: {e}")

print("\n=== python-multipart ===")
try:
    import multipart
    print("  python-multipart INSTALLED")
except ImportError as e:
    print(f"  NOT installed: {e}")

print("\n=== tests directory ===")
for fname in sorted(os.listdir("tests")):
    print(f"  {fname}")

cur.close()
conn.close()
print("\nDone.")
