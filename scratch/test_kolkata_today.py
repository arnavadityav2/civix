import asyncio
from sqlalchemy import text
from civix_api.database import engine

async def test_kolkata_today():
    async with engine.connect() as conn:
        res = await conn.execute(text("""
            WITH case_activity AS (
                SELECT 
                    c.case_id,
                    GREATEST(
                        c.updated_at,
                        c.created_at,
                        emt.max_event_tx,
                        evmt.max_evidence_tx,
                        lmt.max_lead_created
                    ) as last_activity_at
                FROM civix.investigative_case c
                LEFT JOIN (
                    SELECT el.case_id, MAX(e.tx_start) as max_event_tx
                    FROM civix.event_location el
                    JOIN civix.event e ON el.event_id = e.event_id
                    WHERE el.case_id IS NOT NULL
                    GROUP BY el.case_id
                ) emt ON c.case_id = emt.case_id
                LEFT JOIN (
                    SELECT case_id, MAX(tx_start) as max_evidence_tx
                    FROM civix.evidence_instance
                    GROUP BY case_id
                ) evmt ON c.case_id = evmt.case_id
                LEFT JOIN (
                    SELECT case_id, MAX(created_at) as max_lead_created
                    FROM civix.investigative_lead
                    GROUP BY case_id
                ) lmt ON c.case_id = lmt.case_id
            )
            SELECT 
                COUNT(*) FILTER (WHERE (last_activity_at AT TIME ZONE 'Asia/Kolkata')::date = (NOW() AT TIME ZONE 'Asia/Kolkata')::date) as updated_today_kolkata
            FROM case_activity;
        """))
        print("Updated today (Asia/Kolkata):", res.scalar())

if __name__ == "__main__":
    asyncio.run(test_kolkata_today())
