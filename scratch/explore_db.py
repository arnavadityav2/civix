import psycopg2

PG_DSN = "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"

def explore():
    with psycopg2.connect(PG_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT identifier_type, count(*) FROM civix.source_identity GROUP BY identifier_type")
            print("Source Identity Types:", cur.fetchall())
            
            # Find a person and their linked things
            cur.execute("SELECT entity_id, display_name FROM civix.person LIMIT 5")
            persons = cur.fetchall()
            print("\nPersons:", persons)
            
            cur.execute("SELECT participant_role, count(*) FROM civix.event_participant GROUP BY participant_role")
            print("\nEvent Participants:", cur.fetchall())

            cur.execute("SELECT predicate, count(*) FROM civix.assertion GROUP BY predicate")
            print("\nAssertions:", cur.fetchall())

            # Find assertions linking source_identity to phone_number
            cur.execute("""
                SELECT p.display_name, a.predicate, o.msisdn
                FROM civix.person p
                JOIN civix.assertion a ON p.entity_id = a.subject_entity_id
                JOIN civix.phone_number o ON a.object_entity_id = o.entity_id
                LIMIT 5
            """)
            print("\nPerson -> Phone:", cur.fetchall())
            
            cur.execute("""
                SELECT s.raw_identifier, s.identifier_type, a.predicate, o.msisdn
                FROM civix.source_identity s
                JOIN civix.assertion a ON s.entity_id = a.subject_entity_id
                JOIN civix.phone_number o ON a.object_entity_id = o.entity_id
                LIMIT 5
            """)
            print("\nSource Identity -> Phone:", cur.fetchall())

if __name__ == "__main__":
    explore()
