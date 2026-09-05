import asyncio
from sqlalchemy import text
from civix_api.database import engine

async def test_summary_calculation():
    async with engine.connect() as conn:
        query = text("""
            WITH case_base AS (
                SELECT 
                    c.case_id,
                    c.case_number,
                    c.status,
                    c.priority,
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
                COUNT(*) as total_cases,
                COUNT(*) FILTER (WHERE status IN ('ACTIVE', 'OPEN')) as active_cases,
                COUNT(*) FILTER (WHERE priority = 'CRITICAL') as critical_cases,
                COUNT(*) FILTER (WHERE case_number NOT LIKE 'SYN-%') as golden_cases,
                COUNT(*) FILTER (WHERE case_number LIKE 'SYN-%') as synthetic_cases,
                COUNT(*) FILTER (WHERE last_activity_at >= NOW() - INTERVAL '24 hours' OR last_activity_at::date = CURRENT_DATE) as updated_today
            FROM case_base;
        """)
        
        res = await conn.execute(query)
        row = res.fetchone()
        print("=== Summary Query Result ===")
        print(dict(row._mapping))

if __name__ == "__main__":
    asyncio.run(test_summary_calculation())
