import psycopg2

PG_DSN = "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"

def explore():
    with psycopg2.connect(PG_DSN) as conn:
        with conn.cursor() as cur:
            # Check what subject/object OWNS assertion links
            cur.execute("""
                SELECT 
                    s.entity_type as subj_type, 
                    o.entity_type as obj_type, 
                    count(*) 
                FROM civix.assertion a
                JOIN civix.entity s ON a.subject_entity_id = s.entity_id
                JOIN civix.entity o ON a.object_entity_id = o.entity_id
                WHERE a.predicate = 'OWNS'
                GROUP BY s.entity_type, o.entity_type
            """)
            print("OWNS links:", cur.fetchall())

            # Check what subject/object HOLDS_ACCOUNT links
            cur.execute("""
                SELECT 
                    s.entity_type as subj_type, 
                    o.entity_type as obj_type, 
                    count(*) 
                FROM civix.assertion a
                JOIN civix.entity s ON a.subject_entity_id = s.entity_id
                JOIN civix.entity o ON a.object_entity_id = o.entity_id
                WHERE a.predicate = 'HOLDS_ACCOUNT'
                GROUP BY s.entity_type, o.entity_type
            """)
            print("HOLDS_ACCOUNT links:", cur.fetchall())
            
            # Check what events participant roles are linked to
            cur.execute("""
                SELECT 
                    e.event_type, 
                    ep.participant_role, 
                    en.entity_type, 
                    count(*)
                FROM civix.event_participant ep
                JOIN civix.event e ON ep.event_id = e.event_id
                JOIN civix.entity en ON ep.entity_id = en.entity_id
                GROUP BY e.event_type, ep.participant_role, en.entity_type
            """)
            print("\nEvent Links:", cur.fetchall())

            # Check case_entity_role
            cur.execute("""
                SELECT role, e.entity_type, count(*)
                FROM civix.case_entity_role cer
                JOIN civix.entity e ON cer.entity_id = e.entity_id
                GROUP BY role, e.entity_type
            """)
            print("\nCase Roles:", cur.fetchall())


if __name__ == "__main__":
    explore()
