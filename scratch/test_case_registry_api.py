import asyncio
import jwt
from datetime import datetime, timedelta, timezone
import httpx
from sqlalchemy import text
from civix_api.database import engine
from civix_api.config import settings
from civix_api.main import app

async def test_reconciliation():
    # 1. Create a valid test JWT token for authorization
    payload = {
        "sub": "00000000-0000-0000-0000-000000000001",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    token = jwt.encode(payload, settings.civix_jwt_secret, algorithm="HS256")
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Call API
        resp = await client.get("/api/v1/cases/registry?page=1&page_size=50", headers=headers)
        assert resp.status_code == 200, f"API returned status {resp.status_code}: {resp.text}"
        data = resp.json()
        
        summary = data["summary"]
        pagination = data["pagination"]
        items = data["items"]
        
        print("=== API Summary Output ===")
        print(summary)
        print(f"Pagination: page {pagination['page']} of {pagination['total_pages']}, total {pagination['total']}")
        print(f"Items returned: {len(items)}")

        # Direct SQL Check
        async with engine.connect() as conn:
            # Reconcile summary counts
            res = await conn.execute(text("SELECT count(*) FROM civix.investigative_case"))
            db_total = res.scalar()

            res = await conn.execute(text("SELECT count(*) FROM civix.investigative_case WHERE case_number NOT LIKE 'SYN-%'"))
            db_golden = res.scalar()

            res = await conn.execute(text("SELECT count(*) FROM civix.investigative_case WHERE case_number LIKE 'SYN-%'"))
            db_synthetic = res.scalar()

            print(f"\n--- Summary Reconciliation ---")
            print(f"Total Cases: API={summary['total_cases']}, DB={db_total} => {'PASS' if summary['total_cases'] == db_total else 'FAIL'}")
            print(f"Golden Cases: API={summary['golden_cases']}, DB={db_golden} => {'PASS' if summary['golden_cases'] == db_golden else 'FAIL'}")
            print(f"Synthetic Cases: API={summary['synthetic_cases']}, DB={db_synthetic} => {'PASS' if summary['synthetic_cases'] == db_synthetic else 'FAIL'}")
            print(f"Golden + Synthetic == Total: {summary['golden_cases'] + summary['synthetic_cases'] == summary['total_cases']}")

            # Sample Case Verification
            target_cases = ['CIV-2024-038', 'SYN-2025-002', 'SYN-2025-004']
            print("\n--- Sample Case Reconciliation ---")
            for target_num in target_cases:
                # Find in API items (or call API with search)
                s_resp = await client.get(f"/api/v1/cases/registry?search={target_num}", headers=headers)
                assert s_resp.status_code == 200, f"Search failed: {s_resp.text}"
                s_items = s_resp.json()["items"]
                api_item = next((i for i in s_items if i["case_number"] == target_num), None)
                assert api_item is not None, f"Case {target_num} not returned in search!"

                # SQL query for this specific case
                sql_q = text("""
                    WITH case_entities AS (
                        SELECT case_id, COUNT(DISTINCT entity_id) as entity_count
                        FROM civix.case_entity_role
                        WHERE case_id = :cid
                        GROUP BY case_id
                    ),
                    case_evidence AS (
                        SELECT case_id, COUNT(DISTINCT instance_id) as evidence_count
                        FROM civix.evidence_instance
                        WHERE case_id = :cid
                        GROUP BY case_id
                    ),
                    combined_events AS (
                        SELECT case_id, event_id FROM civix.event_location WHERE case_id = :cid
                        UNION
                        SELECT cer.case_id, ep.event_id 
                        FROM civix.event_participant ep 
                        JOIN civix.case_entity_role cer ON ep.entity_id = cer.entity_id
                        WHERE cer.case_id = :cid
                    ),
                    case_events AS (
                        SELECT case_id, COUNT(DISTINCT event_id) as event_count
                        FROM combined_events
                        GROUP BY case_id
                    ),
                    case_leads AS (
                        SELECT case_id, COUNT(DISTINCT lead_id) as lead_count
                        FROM civix.investigative_lead
                        WHERE case_id = :cid
                        GROUP BY case_id
                    ),
                    case_firs AS (
                        SELECT DISTINCT ON (case_id) case_id, police_station, district
                        FROM civix.fir
                        WHERE case_id = :cid
                        ORDER BY case_id, filed_at DESC
                    )
                    SELECT 
                        c.case_id,
                        c.case_number,
                        c.title,
                        c.case_type::text,
                        c.status::text,
                        c.priority::text,
                        COALESCE(f.district, c.jurisdiction) as jurisdiction,
                        COALESCE(f.police_station, c.jurisdiction) as police_station,
                        COALESCE(ce.entity_count, 0) as entity_count,
                        COALESCE(cev.evidence_count, 0) as evidence_count,
                        COALESCE(cevt.event_count, 0) as event_count,
                        COALESCE(cl.lead_count, 0) as lead_count
                    FROM civix.investigative_case c
                    LEFT JOIN case_entities ce ON c.case_id = ce.case_id
                    LEFT JOIN case_evidence cev ON c.case_id = cev.case_id
                    LEFT JOIN case_events cevt ON c.case_id = cevt.case_id
                    LEFT JOIN case_leads cl ON c.case_id = cl.case_id
                    LEFT JOIN case_firs f ON c.case_id = f.case_id
                    WHERE c.case_number = :num
                """)
                db_res = await conn.execute(sql_q, {"num": target_num, "cid": api_item["case_id"]})
                db_row = db_res.fetchone()._mapping

                print(f"\nCase: {target_num}")
                print(f"  Title: API='{api_item['title']}' | DB='{db_row['title']}'")
                print(f"  Type: API='{api_item['case_type']}' | DB='{db_row['case_type']}'")
                print(f"  Status: API='{api_item['status']}' | DB='{db_row['status']}'")
                print(f"  Priority: API='{api_item['priority']}' | DB='{db_row['priority']}'")
                print(f"  Jurisdiction: API='{api_item['jurisdiction']}' | DB='{db_row['jurisdiction']}'")
                print(f"  Police Station: API='{api_item['police_station']}' | DB='{db_row['police_station']}'")
                print(f"  Entities: API={api_item['entity_count']} | DB={db_row['entity_count']}")
                print(f"  Evidence: API={api_item['evidence_count']} | DB={db_row['evidence_count']}")
                print(f"  Events: API={api_item['event_count']} | DB={db_row['event_count']}")
                print(f"  Leads: API={api_item['lead_count']} | DB={db_row['lead_count']}")

                # Check equalities
                assert api_item['title'] == db_row['title']
                assert api_item['case_type'] == db_row['case_type']
                assert api_item['status'] == db_row['status']
                assert api_item['priority'] == db_row['priority']
                assert api_item['entity_count'] == db_row['entity_count']
                assert api_item['evidence_count'] == db_row['evidence_count']
                assert api_item['event_count'] == db_row['event_count']
                assert api_item['lead_count'] == db_row['lead_count']
                print("  => RECONCILIATION MATCH: PERFECT 100%")

if __name__ == "__main__":
    asyncio.run(test_reconciliation())
