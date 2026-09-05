import asyncio
from sqlalchemy import text
from civix_api.database import async_session_maker

async def test_insert():
    async with async_session_maker() as session:
        try:
            res = await session.execute(text("SELECT case_id FROM civix.cases LIMIT 1"))
            case_id = res.first()[0]
            
            from uuid import uuid4
            job_id = uuid4()
            ures = await session.execute(text("SELECT user_id FROM civix.users LIMIT 1"))
            user_id = ures.first()[0]
            
            any_veh = await session.execute(text("SELECT entity_id FROM civix.vehicle LIMIT 1"))
            target_vid = any_veh.first()[0]
            
            await session.execute(
                text("""
                    INSERT INTO civix.cctv_search_job (
                        job_id, case_id, requested_by, target_vehicle_id, camera_ids, start_time, end_time, status
                    ) VALUES (
                        :jid, :cid, :uid, :vid, :cams, :start, :end, 'STARTING'
                    )
                """),
                {
                    'jid': job_id,
                    'cid': case_id,
                    'uid': user_id,
                    'vid': target_vid,
                    'cams': ['c0c70025-0009-4000-8000-000000000009'],
                    'start': '2026-09-04T12:00:00Z',
                    'end': '2026-09-04T14:00:00Z'
                }
            )
            await session.commit()
            print('Success')
        except Exception as e:
            print(f'Error: {type(e).__name__}: {e}')

asyncio.run(test_insert())
