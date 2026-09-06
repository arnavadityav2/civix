import psycopg2
import jwt
import requests
from datetime import datetime, timedelta, timezone
from civix_api.config import settings

def main():
    conn = psycopg2.connect(dbname='civix_demo', user='postgres', password='postgres', host='localhost', port=5432)
    cur = conn.cursor()

    cur.execute("""
        UPDATE civix.location 
        SET location_type = 'CELL_SECTOR_POLYGON'
        WHERE entity_id IN (
            SELECT location_id FROM civix.event_location WHERE case_id = '1346a86d-267a-a635-9d62-e34c76ecd24f'
        )
    """)
    conn.commit()
    print("Updated location_type for CIV-2012-001 locations to CELL_SECTOR_POLYGON!")

    # Also register case entities in case_entity_role for PHONE_NUMBER if missing
    cur.execute("""
        SELECT entity_id FROM civix.phone_number
    """)
    p_entities = [r[0] for r in cur.fetchall()]

    for pe in p_entities:
        cur.execute("""
            INSERT INTO civix.case_entity_role (case_id, entity_id, role)
            SELECT '1346a86d-267a-a635-9d62-e34c76ecd24f'::uuid, %s::uuid, 'PERSON_OF_INTEREST'::civix.case_entity_role_enum
            WHERE NOT EXISTS (
                SELECT 1 FROM civix.case_entity_role WHERE case_id = '1346a86d-267a-a635-9d62-e34c76ecd24f' AND entity_id = %s
            )
        """, (pe, pe))

    conn.commit()
    print("Registered phone entities in case_entity_role!")

    cur.close()
    conn.close()

    # Now test API endpoints!
    secret = settings.civix_jwt_secret
    token = jwt.encode({'sub': '00000000-0000-0000-0000-000000000001', 'username': 'admin', 'exp': datetime.now(timezone.utc) + timedelta(days=1), 'role': 'INVESTIGATOR'}, secret, algorithm='HS256')
    headers = {'Authorization': f'Bearer {token}'}
    baseUrl = 'http://127.0.0.1:8000/api/v1'

    res_towers = requests.get(f'{baseUrl}/cases/CIV-2012-001/telecom/towers', headers=headers)
    print("API Towers count:", len(res_towers.json().get('towers', [])))
    print("API Towers data:", res_towers.json())

    res_entities = requests.get(f'{baseUrl}/cases/CIV-2012-001/telecom/entities', headers=headers)
    print("API Entities count:", len(res_entities.json().get('items', [])))
    print("API Entities data:", res_entities.json())

if __name__ == "__main__":
    main()
