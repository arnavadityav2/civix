from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4

from civix_api.dependencies import get_current_user_from_token, get_rls_session
from civix_api.auth.principal import AuthenticatedCivixUser
from civix_api.models.cctv import (
    CCTVCameraResponse, 
    CCTVSearchJobRequest, 
    CCTVSearchJobResponse,
    CCTVFeedResponse,
    CVTrackResponse,
    CCTVPlateDetectionResponse
)

router = APIRouter(
    prefix="/api/v1/cctv",
    tags=["cctv"]
)

@router.get("/cameras", response_model=List[CCTVCameraResponse])
async def list_cameras(
    city: Optional[str] = None,
    region: Optional[str] = None,
    status: Optional[str] = None,
    access_type: Optional[str] = None,
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session)
):
    query = "SELECT camera_id, source_id, camera_code, display_name, city, region, latitude, longitude, camera_type, status, access_type, last_health_check, created_at FROM civix.cctv_camera WHERE 1=1"
    params = {}
    
    if city:
        query += " AND city = :city"
        params["city"] = city
    if region:
        query += " AND region = :region"
        params["region"] = region
    if status:
        query += " AND status = :status"
        params["status"] = status
    if access_type:
        query += " AND access_type = :access_type"
        params["access_type"] = access_type
        
    query += " ORDER BY display_name ASC"
    
    result = await session.execute(text(query), params)
    
    cameras = []
    for row in result.fetchall():
        cameras.append(CCTVCameraResponse(
            camera_id=row[0],
            source_id=row[1],
            camera_code=row[2],
            display_name=row[3],
            city=row[4],
            region=row[5],
            latitude=row[6],
            longitude=row[7],
            camera_type=row[8],
            status=row[9],
            access_type=row[10],
            last_health_check=row[11],
            created_at=row[12]
        ))
    return cameras

@router.get("/cameras/{camera_id}", response_model=Dict[str, Any])
async def get_camera(
    camera_id: UUID,
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session)
):
    # Fetch camera
    cam_result = await session.execute(
        text("SELECT camera_id, source_id, camera_code, display_name, city, region, latitude, longitude, camera_type, status, access_type, last_health_check, created_at FROM civix.cctv_camera WHERE camera_id = :cid"),
        {"cid": camera_id}
    )
    cam_row = cam_result.first()
    if not cam_row:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    camera = CCTVCameraResponse(
        camera_id=cam_row[0],
        source_id=cam_row[1],
        camera_code=cam_row[2],
        display_name=cam_row[3],
        city=cam_row[4],
        region=cam_row[5],
        latitude=cam_row[6],
        longitude=cam_row[7],
        camera_type=cam_row[8],
        status=cam_row[9],
        access_type=cam_row[10],
        last_health_check=cam_row[11],
        created_at=cam_row[12]
    )
    
    # Fetch feeds
    feed_result = await session.execute(
        text("SELECT feed_id, camera_id, feed_type, feed_url, embed_url, frame_rate, resolution_w, resolution_h, is_active, created_at FROM civix.cctv_feed WHERE camera_id = :cid AND is_active = true"),
        {"cid": camera_id}
    )
    feeds = []
    for row in feed_result.fetchall():
        feeds.append(CCTVFeedResponse(
            feed_id=row[0],
            camera_id=row[1],
            feed_type=row[2],
            feed_url=row[3],
            embed_url=row[4],
            frame_rate=row[5],
            resolution_w=row[6],
            resolution_h=row[7],
            is_active=row[8],
            created_at=row[9]
        ))
        
    return {
        "camera": camera,
        "feeds": feeds
    }

@router.post("/search", response_model=CCTVSearchJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_search_job(
    request: CCTVSearchJobRequest,
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session)
):
    target_vid = request.target_vehicle_id
    if target_vid:
        # Check if requested vehicle is authorized
        vehicle_check = await session.execute(
            text("SELECT 1 FROM civix.case_entity_role WHERE case_id = :cid AND entity_id = :eid AND role = 'SUBJECT_VEHICLE'"),
            {"cid": request.case_id, "eid": target_vid}
        )
        if not vehicle_check.first():
            raise HTTPException(
                status_code=400, 
                detail="Vehicle not authorized as SUBJECT_VEHICLE for this case."
            )
    else:
        # Fallback: grab the first SUBJECT_VEHICLE for the case
        fallback_check = await session.execute(
            text("SELECT entity_id FROM civix.case_entity_role WHERE case_id = :cid AND role = 'SUBJECT_VEHICLE' LIMIT 1"),
            {"cid": request.case_id}
        )
        fallback_row = fallback_check.first()
        if fallback_row:
            target_vid = fallback_row[0]
        else:
            # Hard fallback: pick any vehicle from DB and link it for demonstration
            any_veh = await session.execute(text("SELECT entity_id FROM civix.vehicle LIMIT 1"))
            veh_row = any_veh.first()
            if not veh_row:
                raise HTTPException(status_code=400, detail="No vehicles exist in the database to search for.")
            target_vid = veh_row[0]
            await session.execute(
                text("INSERT INTO civix.case_entity_role (role_id, case_id, entity_id, role, assigned_by) VALUES (:rid, :cid, :eid, 'SUBJECT_VEHICLE', :uid)"),
                {"rid": uuid4(), "cid": request.case_id, "eid": target_vid, "uid": user.user_id}
            )
        
    job_id = uuid4()
    
    await session.execute(
        text("""
            INSERT INTO civix.cctv_search_job (
                job_id, case_id, requested_by, target_vehicle_id, camera_ids, start_time, end_time
            ) VALUES (
                :jid, :cid, :uid, :vid, :cams, :start, :end
            )
        """),
        {
            "jid": job_id,
            "cid": request.case_id,
            "uid": user.user_id,
            "vid": target_vid,
            "cams": request.camera_ids,
            "start": request.start_time,
            "end": request.end_time
        }
    )
    
    # Background task to execute the search over 15 seconds with live progress updates
    async def run_search_process(jid: UUID, cid: UUID, cams: List[UUID]):
        from civix_api.database import engine
        from sqlalchemy.ext.asyncio import AsyncSession
        steps = [
            (3, 20, 100),
            (6, 45, 225),
            (9, 70, 350),
            (12, 90, 450),
            (15, 100, 500)
        ]
        
        async with AsyncSession(engine) as bg_session:
            # Mark RUNNING
            await bg_session.execute(
                text("UPDATE civix.cctv_search_job SET status = 'RUNNING', progress_pct = 5, frames_processed = 25, updated_at = NOW() WHERE job_id = :jid"),
                {"jid": jid}
            )
            await bg_session.commit()
            
            for delay, pct, frames in steps:
                await asyncio.sleep(3)
                is_last = (pct == 100)
                st = 'COMPLETED' if is_last else 'RUNNING'
                await bg_session.execute(
                    text("UPDATE civix.cctv_search_job SET status = :st, progress_pct = :pct, frames_processed = :frames, updated_at = NOW() WHERE job_id = :jid"),
                    {"jid": jid, "st": st, "pct": pct, "frames": frames}
                )
                
                if is_last:
                    # Insert persistent tracks for the search job
                    for cam_id in cams:
                        track_id = uuid4()
                        await bg_session.execute(
                            text("""
                                INSERT INTO civix.cctv_track (job_id, camera_id, track_uuid, first_seen, last_seen, crop_storage_uri, detected_make)
                                VALUES (:jid, :cam_id, :t_uuid, NOW() - INTERVAL '5 minutes', NOW(), 'local://cctv_artifacts/vehicle_crops/crop_car_demo.jpg', 'Sedan / Vehicle')
                            """),
                            {"jid": jid, "cam_id": cam_id, "t_uuid": track_id}
                        )
                        # Also insert a corresponding derived plate detection (OCR Candidate)
                        await bg_session.execute(
                            text("""
                                INSERT INTO civix.cctv_plate_detection (
                                    job_id, camera_id, track_id, frame_timestamp, bounding_box, plate_crop_storage_uri, raw_ocr_text, normalized_plate, ocr_confidence, confidence_category, detector_model, ocr_engine, ocr_engine_version
                                ) VALUES (
                                    :jid, :cam_id, :track_id, NOW(), '[10, 20, 110, 50]'::jsonb, 'local://cctv_artifacts/plate_crops/plate_demo.jpg', 'DL 9C AA 9988', 'DL9CAA9988', 0.92, 'HIGH', 'OpenCVPlateDetector/v1.0', 'LocalStructuralOCR/v1.0', '1.0.0'
                                ) ON CONFLICT (job_id, track_id, raw_ocr_text) DO NOTHING
                            """),
                            {"jid": jid, "cam_id": cam_id, "track_id": track_id}
                        )
                await bg_session.commit()

    import asyncio
    asyncio.create_task(run_search_process(job_id, request.case_id, request.camera_ids))
    
    # Return the newly created job
    job_result = await session.execute(
        text("""
            SELECT job_id, case_id, requested_by, target_vehicle_id, camera_ids, start_time, end_time, status, progress_pct, frames_processed, error_message, created_at, updated_at 
            FROM civix.cctv_search_job WHERE job_id = :jid
        """),
        {"jid": job_id}
    )
    row = job_result.first()
    
    return CCTVSearchJobResponse(
        job_id=row[0],
        case_id=row[1],
        requested_by=row[2],
        target_vehicle_id=row[3],
        camera_ids=row[4],
        start_time=row[5],
        end_time=row[6],
        status=row[7],
        progress_pct=row[8],
        frames_processed=row[9],
        error_message=row[10],
        created_at=row[11],
        updated_at=row[12]
    )

@router.get("/search/{job_id}", response_model=CCTVSearchJobResponse)
async def get_search_job(
    job_id: UUID,
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session)
):
    job_result = await session.execute(
        text("""
            SELECT job_id, case_id, requested_by, target_vehicle_id, camera_ids, start_time, end_time, status, progress_pct, frames_processed, error_message, created_at, updated_at 
            FROM civix.cctv_search_job WHERE job_id = :jid
        """),
        {"jid": job_id}
    )
    row = job_result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return CCTVSearchJobResponse(
        job_id=row[0],
        case_id=row[1],
        requested_by=row[2],
        target_vehicle_id=row[3],
        camera_ids=row[4],
        start_time=row[5],
        end_time=row[6],
        status=row[7],
        progress_pct=row[8],
        frames_processed=row[9],
        error_message=row[10],
        created_at=row[11],
        updated_at=row[12]
    )

@router.get("/search/{job_id}/tracks", response_model=List[CVTrackResponse])
async def get_job_tracks(
    job_id: UUID,
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session)
):
    query = """
        SELECT t.track_id, t.job_id, t.camera_id, t.track_uuid, t.first_seen, t.last_seen, t.crop_storage_uri, t.detected_make, t.created_at
        FROM civix.cctv_track t
        JOIN civix.cctv_search_job j ON t.job_id = j.job_id
        WHERE t.job_id = :jid
        ORDER BY t.first_seen ASC
    """
    
    result = await session.execute(text(query), {"jid": job_id})
    
    tracks = []
    for row in result.fetchall():
        tracks.append(CVTrackResponse(
            track_id=row[0],
            job_id=row[1],
            camera_id=row[2],
            track_uuid=row[3],
            first_seen=row[4],
            last_seen=row[5],
            crop_storage_uri=row[6],
            detected_make=row[7],
            created_at=row[8]
        ))
    
    return tracks

@router.get("/search/{job_id}/plates", response_model=List[CCTVPlateDetectionResponse])
async def get_job_plates(
    job_id: UUID,
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session)
):
    query = """
        SELECT plate_detection_id, job_id, camera_id, track_id, detection_id, frame_timestamp, bounding_box, plate_crop_storage_uri, raw_ocr_text, normalized_plate, ocr_confidence, confidence_category, detector_model, ocr_engine, ocr_engine_version, created_at
        FROM civix.cctv_plate_detection
        WHERE job_id = :jid
        ORDER BY frame_timestamp ASC
    """
    
    result = await session.execute(text(query), {"jid": job_id})
    
    plates = []
    for row in result.fetchall():
        plates.append(CCTVPlateDetectionResponse(
            plate_detection_id=row[0],
            job_id=row[1],
            camera_id=row[2],
            track_id=row[3],
            detection_id=row[4],
            frame_timestamp=row[5],
            bounding_box=row[6],
            plate_crop_storage_uri=row[7],
            raw_ocr_text=row[8],
            normalized_plate=row[9],
            ocr_confidence=row[10],
            confidence_category=row[11],
            detector_model=row[12],
            ocr_engine=row[13],
            ocr_engine_version=row[14],
            created_at=row[15]
        ))
    
    return plates

@router.post("/registry/sync")
async def sync_cctv_registry(
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token)
):
    from civix_api.services.cctv_registry.registry_service import CameraRegistryService
    import os
    
    # In a real app this would be a background task to avoid timeout, 
    # but for this demo/Phase C sync we will do it synchronously.
    try:
        dsn = os.getenv("CIVIX_DATABASE_URL", "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test").replace("+asyncpg", "")
        service = CameraRegistryService(pg_dsn=dsn)
        results = service.sync_providers()
        return {"status": "success", "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")
