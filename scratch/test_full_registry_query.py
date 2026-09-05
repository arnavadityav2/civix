import asyncio
import time
from sqlalchemy import text
from civix_api.database import engine

async def test_full_registry_query():
    async with engine.connect() as conn:
        t0 = time.perf_counter()
        
        # 1. Items + Pagination
        items_query = text("""
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
            combined_events AS (
                SELECT case_id, event_id FROM civix.event_location WHERE case_id IS NOT NULL
                UNION
                SELECT cer.case_id, ep.event_id 
                FROM civix.event_participant ep 
                JOIN civix.case_entity_role cer ON ep.entity_id = cer.entity_id
            ),
            case_events AS (
                SELECT case_id, COUNT(DISTINCT event_id) as event_count
                FROM combined_events
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
            enriched_cases AS (
                SELECT 
                    c.case_id,
                    c.case_number,
                    c.title,
                    c.investigating_unit as description,
                    c.case_type::text as case_type,
                    c.status::text as status,
                    c.priority::text as priority,
                    COALESCE(f.district, c.jurisdiction) as jurisdiction,
                    COALESCE(f.police_station, c.jurisdiction) as police_station,
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
                    CASE WHEN c.case_number LIKE 'SYN-%' THEN 'SYNTHETIC' ELSE 'GOLDEN' END as provenance,
                    CASE WHEN c.case_number LIKE 'SYN-%' THEN 'SYNTHETIC_BENCHMARK' ELSE 'HERO_INVESTIGATION' END as source_type
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
            SELECT COUNT(*) OVER() as filtered_total, * 
            FROM enriched_cases c
            ORDER BY last_activity_at DESC NULLS LAST
            LIMIT 50 OFFSET 0;
        """)
        res = await conn.execute(items_query)
        rows = res.fetchall()
        filtered_total = rows[0][0] if rows else 0
        
        # 2. Summary query
        summary_query = text("""
            WITH event_max_time AS (
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
            )
            SELECT
                COUNT(*) as total_cases,
                COUNT(*) FILTER (WHERE c.status::text IN ('ACTIVE', 'OPEN')) as active_cases,
                COUNT(*) FILTER (WHERE c.priority::text = 'CRITICAL') as critical_cases,
                COUNT(*) FILTER (WHERE c.case_number NOT LIKE 'SYN-%') as golden_cases,
                COUNT(*) FILTER (WHERE c.case_number LIKE 'SYN-%') as synthetic_cases,
                COUNT(*) FILTER (WHERE (GREATEST(
                    c.updated_at,
                    c.created_at,
                    emt.max_event_tx,
                    evmt.max_evidence_tx,
                    lmt.max_lead_created
                ) AT TIME ZONE 'Asia/Kolkata')::date = (NOW() AT TIME ZONE 'Asia/Kolkata')::date) as updated_today
            FROM civix.investigative_case c
            LEFT JOIN event_max_time emt ON c.case_id = emt.case_id
            LEFT JOIN evidence_max_time evmt ON c.case_id = evmt.case_id
            LEFT JOIN lead_max_time lmt ON c.case_id = lmt.case_id;
        """)
        sum_res = await conn.execute(summary_query)
        summary_row = sum_res.fetchone()
        
        t1 = time.perf_counter()
        print(f"Full execution time: {(t1 - t0)*1000:.2f} ms")
        print(f"Items returned: {len(rows)}, Filtered total: {filtered_total}")
        print(f"Summary stats: {dict(summary_row._mapping)}")
        print("\nSample first row:", dict(rows[0]._mapping))

if __name__ == "__main__":
    asyncio.run(test_full_registry_query())
