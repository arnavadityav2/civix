import asyncio
import time
from sqlalchemy import text
from civix_api.database import engine

async def benchmark_query():
    async with engine.connect() as conn:
        t0 = time.perf_counter()
        
        # CTE query for items + summary
        query = text("""
            WITH case_entities AS (
                SELECT case_id, COUNT(DISTINCT entity_id) as entity_count
                FROM civix.case_entity_role
                GROUP BY case_id
            ),
            case_evidence AS (
                SELECT case_id, COUNT(DISTINCT instance_id) as evidence_count
                FROM civix.evidence_instance
                GROUP BY case_id
            ),
            case_events AS (
                SELECT case_id, COUNT(DISTINCT event_id) as event_count
                FROM civix.event_location
                WHERE case_id IS NOT NULL
                GROUP BY case_id
            ),
            case_leads AS (
                SELECT case_id, COUNT(DISTINCT lead_id) as lead_count
                FROM civix.investigative_lead
                GROUP BY case_id
            ),
            case_firs AS (
                SELECT DISTINCT ON (case_id) case_id, police_station, district
                FROM civix.fir
                ORDER BY case_id, filed_at DESC
            ),
            event_max_time AS (
                SELECT el.case_id, MAX(e.tx_start) as max_event_tx
                FROM civix.event_location el
                JOIN civix.event e ON el.event_id = e.event_id
                WHERE el.case_id IS NOT NULL
                GROUP BY el.case_id
            ),
            evidence_max_time AS (
                SELECT case_id, MAX(tx_start) as max_evidence_tx
                FROM civix.evidence_instance
                GROUP BY case_id
            ),
            lead_max_time AS (
                SELECT case_id, MAX(created_at) as max_lead_created
                FROM civix.investigative_lead
                GROUP BY case_id
            ),
            filtered_cases AS (
                SELECT 
                    c.case_id,
                    c.case_number,
                    c.title,
                    c.case_type,
                    c.status,
                    c.priority,
                    c.jurisdiction,
                    c.investigating_unit,
                    f.police_station,
                    f.district,
                    COALESCE(ce.entity_count, 0) as entity_count,
                    COALESCE(cev.evidence_count, 0) as evidence_count,
                    COALESCE(cevt.event_count, 0) as event_count,
                    COALESCE(cl.lead_count, 0) as lead_count,
                    GREATEST(
                        c.updated_at,
                        c.created_at,
                        emt.max_event_tx,
                        evmt.max_evidence_tx,
                        lmt.max_lead_created
                    ) as last_activity_at,
                    c.created_at,
                    c.updated_at,
                    CASE WHEN c.case_number LIKE 'SYN-%' THEN 'SYNTHETIC' ELSE 'GOLDEN' END as provenance
                FROM civix.investigative_case c
                LEFT JOIN case_entities ce ON c.case_id = ce.case_id
                LEFT JOIN case_evidence cev ON c.case_id = cev.case_id
                LEFT JOIN case_events cevt ON c.case_id = cevt.case_id
                LEFT JOIN case_leads cl ON c.case_id = cl.case_id
                LEFT JOIN case_firs f ON c.case_id = f.case_id
                LEFT JOIN event_max_time emt ON c.case_id = emt.case_id
                LEFT JOIN evidence_max_time evmt ON c.case_id = evmt.case_id
                LEFT JOIN lead_max_time lmt ON c.case_id = lmt.case_id
            )
            SELECT * FROM filtered_cases
            ORDER BY last_activity_at DESC NULLS LAST
            LIMIT 50 OFFSET 0;
        """)
        res = await conn.execute(query)
        rows = res.fetchall()
        t1 = time.perf_counter()
        print(f"Items query executed in {(t1 - t0)*1000:.2f} ms, returned {len(rows)} rows")

if __name__ == "__main__":
    asyncio.run(benchmark_query())
