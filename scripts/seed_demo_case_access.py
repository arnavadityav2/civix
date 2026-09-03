import psycopg2

def seed_demo_case_access():
    print("==========================================================")
    print("SEEDING DEMO CASE ACCESS FOR ADMIN USER")
    print("==========================================================")
    
    conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
    cur = conn.cursor()
    
    admin_user_id = "00000000-0000-0000-0000-000000000001"
    
    # Grant ADMIN case access for all 250 cases
    cur.execute("""
        INSERT INTO civix.case_access (access_id, case_id, user_id, permission_level, granted_by)
        SELECT 
            gen_random_uuid(),
            case_id,
            %s::uuid,
            'ADMIN',
            %s::uuid
        FROM civix.investigative_case
        ON CONFLICT DO NOTHING;
    """, (admin_user_id, admin_user_id))
    
    conn.commit()
    
    cur.execute("SELECT count(*) FROM civix.case_access WHERE user_id = %s::uuid;", (admin_user_id,))
    cnt = cur.fetchone()[0]
    print(f"[PASS] Granted ADMIN access for {cnt} cases to user {admin_user_id}")
    
    conn.close()

if __name__ == "__main__":
    seed_demo_case_access()
