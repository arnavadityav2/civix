import psycopg2
import uuid

def update_phantom_route_geometry():
    conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
    cur = conn.cursor()

    loc_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, "civix.location.LOC_PHANTOM_ROUTE"))

    cur.execute("""
        UPDATE civix.location
        SET geometry = ST_SetSRID(ST_MakeLine(ST_MakePoint(77.2600, 28.5680), ST_MakePoint(77.2750, 28.5350)), 4326)
        WHERE entity_id = %s;
    """, (loc_uuid,))
    print(f"Updated {cur.rowcount} location row to ST_LineString for LOC_PHANTOM_ROUTE.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    update_phantom_route_geometry()
