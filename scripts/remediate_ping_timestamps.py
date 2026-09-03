import psycopg2
import uuid

def fix_ping_timestamps():
    conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
    cur = conn.cursor()

    ping_events = [
        ("EV_RED_03", "2026-02-12T14:20:00Z", "2026-02-12T14:20:01Z"),
        ("EV_SHELL_03", "2026-03-05T16:15:00Z", "2026-03-05T16:15:01Z"),
        ("EV_MIRAGE_03", "2026-05-02T11:35:00Z", "2026-05-02T11:35:01Z"),
    ]

    for ev_code, st, et in ping_events:
        ev_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"civix.event.{ev_code}"))
        cur.execute("""
            UPDATE civix.event
            SET occurred_at = tstzrange(%s::timestamptz, %s::timestamptz, '[)')
            WHERE event_id = %s;
        """, (st, et, ev_uuid))
        print(f"Updated timestamp for {ev_code} ({ev_uuid}).")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    fix_ping_timestamps()
