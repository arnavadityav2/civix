import psycopg2
import uuid

def test_rls_global_cases():
    conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
    cur = conn.cursor()

    # Create temporary non-admin user
    test_ext_id = f"ext_audit_{uuid.uuid4().hex[:8]}"
    test_uname = f"uname_audit_{uuid.uuid4().hex[:8]}"
    
    cur.execute("""
        INSERT INTO civix.civix_user (external_auth_id, username, display_name, role, clearance_level)
        VALUES (%s, %s, 'RLS Audit User', 'INVESTIGATOR', 'SECRET')
        RETURNING user_id;
    """, (test_ext_id, test_uname))
    uid = cur.fetchone()[0]
    conn.commit()

    # Enable RLS role
    cur.execute("DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'test_rls_role') THEN CREATE ROLE test_rls_role NOSUPERUSER INHERIT NOLOGIN; GRANT USAGE ON SCHEMA civix TO test_rls_role; GRANT SELECT ON ALL TABLES IN SCHEMA civix TO test_rls_role; END IF; END $$;")
    conn.commit()

    cur.execute("SET ROLE test_rls_role;")
    cur.execute(f"SET app.current_user_id = '{uid}';")

    # Run get_spatial_cases query as un-granted investigator
    cur.execute("""
        SELECT 
            c.case_id::text, c.case_number, count(DISTINCT el.event_id)
        FROM civix.investigative_case c
        JOIN civix.event_location el ON c.case_id = el.case_id
        JOIN civix.location l ON el.location_id = l.entity_id
        GROUP BY c.case_id, c.case_number;
    """)
    unauth_rows = cur.fetchall()
    print(f"Un-granted investigator sees {len(unauth_rows)} cases in global query.")

    # Reset role & clean up
    cur.execute("RESET ROLE;")
    cur.execute("SET app.current_user_id = '';")
    cur.execute("DELETE FROM civix.civix_user WHERE user_id = %s;", (uid,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    test_rls_global_cases()
