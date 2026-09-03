import psycopg2

def seed_demo_frontend_user():
    print("==========================================================")
    print("SEEDING FRONTEND DEV USER & CASE ACCESS IN CIVIX_DEMO")
    print("==========================================================")
    
    conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
    cur = conn.cursor()
    
    dev_user_id = "55284c17-1d58-461f-94f5-86c2a5215100"
    admin_user_id = "00000000-0000-0000-0000-000000000001"
    
    # 1. Insert dev user
    cur.execute("""
        INSERT INTO civix.civix_user (user_id, username, display_name, role, clearance_level, external_auth_id)
        VALUES (%s::uuid, 'user_9ac07e01', 'Lead Investigator', 'ADMIN', 'SECRET', 'auth_dev_9ac07e01')
        ON CONFLICT (user_id) DO UPDATE SET role = 'ADMIN', clearance_level = 'SECRET';
    """, (dev_user_id,))
    
    # 2. Insert admin user
    cur.execute("""
        INSERT INTO civix.civix_user (user_id, username, display_name, role, clearance_level, external_auth_id)
        VALUES (%s::uuid, 'civix_system', 'CIVIX System Admin', 'ADMIN', 'SECRET', 'auth_system_admin')
        ON CONFLICT (user_id) DO UPDATE SET role = 'ADMIN', clearance_level = 'SECRET';
    """, (admin_user_id,))
    
    # 3. Grant ADMIN case access for dev user across all 250 cases
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
    """, (dev_user_id, dev_user_id))
    
    # 4. Grant ADMIN case access for admin user across all 250 cases
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
    
    cur.execute("SELECT count(*) FROM civix.case_access WHERE user_id = %s::uuid;", (dev_user_id,))
    cnt = cur.fetchone()[0]
    print(f"[PASS] Successfully granted ADMIN access for {cnt} cases to dev user {dev_user_id}")
    
    conn.close()

if __name__ == "__main__":
    seed_demo_frontend_user()
