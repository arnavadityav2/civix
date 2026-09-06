import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    
    rows = await conn.fetch("""
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
                c.priority::text as priority,
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
            LEFT JOIN event_max_time emt ON c.case_id = emt.case_id
            LEFT JOIN evidence_max_time evmt ON c.case_id = evmt.case_id
            LEFT JOIN lead_max_time lmt ON c.case_id = lmt.case_id
        )
        SELECT case_id, case_number, title, priority, last_activity_at, provenance, updated_at
        FROM enriched_cases
        ORDER BY last_activity_at DESC
        LIMIT 10;
    """)
    
    print("=== TOP 10 CASES BY LAST_ACTIVITY_AT DESC ===")
    for i, r in enumerate(rows, 1):
        print(f"{i:2d}. [{r['case_number']}] {r['title'][:40]:<40} | Activity: {r['last_activity_at']} | Prov: {r['provenance']}")
        
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
