from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, List, Dict, Any
from uuid import UUID
import json

from ..dependencies import get_rls_session
from ..auth.principal import AuthenticatedCivixUser
from ..dependencies import get_current_user_from_token

router = APIRouter(
    prefix="/api/v1/spatial",
    tags=["spatial"]
)

def parse_and_validate_bbox(bbox_str: Optional[str]) -> Optional[tuple]:
    """
    Parses and strictly validates a bounding box string in format: min_lon,min_lat,max_lon,max_lat.
    Rejects malformed, non-numeric, or inverted bounding boxes.
    """
    if not bbox_str:
        return None

    try:
        parts = [float(p.strip()) for p in bbox_str.split(",")]
        if len(parts) != 4:
            raise ValueError("bbox must contain exactly 4 comma-separated values")
        
        min_lon, min_lat, max_lon, max_lat = parts

        if not (-180.0 <= min_lon <= 180.0 and -180.0 <= max_lon <= 180.0):
            raise ValueError("Longitude must be between -180 and 180 degrees")
        if not (-90.0 <= min_lat <= 90.0 and -90.0 <= max_lat <= 90.0):
            raise ValueError("Latitude must be between -90 and 90 degrees")

        if min_lon >= max_lon:
            raise ValueError("min_lon must be strictly less than max_lon")
        if min_lat >= max_lat:
            raise ValueError("min_lat must be strictly less than max_lat")

        return (min_lon, min_lat, max_lon, max_lat)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid bbox parameter: {str(e)}"
        )


@router.get("/cases", response_model=Dict[str, Any])
async def get_spatial_cases(
    bbox: Optional[str] = Query(None, description="min_lon,min_lat,max_lon,max_lat"),
    status: Optional[str] = Query(None, description="Filter by case status"),
    priority: Optional[str] = Query(None, description="Filter by case priority"),
    case_type: Optional[str] = Query(None, description="Filter by case type"),
    search: Optional[str] = Query(None, description="Search cases by title, number or ID"),
    limit: int = Query(100, ge=1, le=250, description="Max cases to return"),
    session: AsyncSession = Depends(get_rls_session)
):
    """
    Returns a GeoJSON FeatureCollection of cases with spatial footprints within the NCR viewport.
    Each feature exposes CASE_FOOTPRINT_CENTROID semantics derived from PostGIS location geometries.
    Explicitly scoped by user case access permissions (Gate 11E-R3).
    """
    bbox_coords = parse_and_validate_bbox(bbox)

    # Base query calculating centroid of all case events with explicit case access filter
    sql = """
        SELECT 
            c.case_id::text,
            c.case_number,
            c.title,
            c.status,
            c.priority,
            c.case_type,
            count(DISTINCT el.event_id) as event_count,
            ST_X(ST_Centroid(ST_Collect(l.geometry))) as centroid_lon,
            ST_Y(ST_Centroid(ST_Collect(l.geometry))) as centroid_lat
        FROM civix.investigative_case c
        JOIN civix.event_location el ON c.case_id = el.case_id
        JOIN civix.location l ON el.location_id = l.entity_id
        WHERE (c.case_id = ANY(civix.get_accessible_case_ids()) OR civix.current_user_is_admin())
    """
    params: Dict[str, Any] = {"limit": limit}

    if status:
        sql += " AND c.status = :status"
        params["status"] = status
    if priority:
        sql += " AND c.priority = :priority"
        params["priority"] = priority
    if case_type:
        sql += " AND c.case_type = :case_type"
        params["case_type"] = case_type

    if search:
        sql += " AND (c.title ILIKE :search OR c.case_number ILIKE :search OR c.case_id::text ILIKE :search)"
        params["search"] = f"%{search}%"

    sql += """
        GROUP BY c.case_id, c.case_number, c.title, c.status, c.priority, c.case_type, c.created_at
        ORDER BY c.created_at DESC
        LIMIT :limit
    """

    result = await session.execute(text(sql), params)
    rows = result.fetchall()

    features = []
    for r in rows:
        cid, cnum, title, cstat, cprio, ctype, ev_cnt, lon, lat = r
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(lon), float(lat)]
            },
            "properties": {
                "case_id": cid,
                "case_number": cnum,
                "title": title,
                "status": cstat,
                "priority": cprio,
                "case_type": ctype,
                "event_count": int(ev_cnt),
                "spatial_semantic": "CASE_FOOTPRINT_CENTROID"
            }
        })

    return {
        "type": "FeatureCollection",
        "features": features
    }


@router.get("/cases/{case_id}/events", response_model=Dict[str, Any])
async def get_case_spatial_events(
    case_id: UUID,
    bbox: Optional[str] = Query(None, description="min_lon,min_lat,max_lon,max_lat"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(100, ge=1, le=500, description="Max event locations to return"),
    session: AsyncSession = Depends(get_rls_session)
):
    """
    Returns a GeoJSON FeatureCollection of spatial events anchored to an authorized investigative case.
    Dynamic provenance derived from Database (Gate 11E-R1).
    Native PostGIS ST_AsGeoJSON geometry serialization (Gate 11E-R2).
    """
    bbox_coords = parse_and_validate_bbox(bbox)

    # Verify case access via RLS-scoped check
    case_check = await session.execute(
        text("""
            SELECT case_id FROM civix.investigative_case 
            WHERE case_id = :cid 
              AND (case_id = ANY(civix.get_accessible_case_ids()) OR civix.current_user_is_admin())
        """),
        {"cid": str(case_id)}
    )
    if not case_check.first():
        # Unauthorized or non-existent case returns 404 to avoid leaking existence
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investigative case not found or access denied"
        )

    sql = """
        SELECT 
            el.event_location_id::text,
            el.event_id::text,
            e.event_type,
            lower(e.occurred_at)::text as event_start,
            upper(e.occurred_at)::text as event_end,
            upper_inf(e.occurred_at) as is_open_ended,
            el.location_id::text,
            l.location_name,
            l.location_type,
            el.location_predicate,
            el.epistemic_status,
            el.case_id::text,
            el.source_record_id::text,
            el.generation_run_id::text,
            gr.generator_version as generation_origin,
            ST_AsGeoJSON(l.geometry) as geojson_geom
        FROM civix.event_location el
        JOIN civix.event e ON el.event_id = e.event_id
        JOIN civix.location l ON el.location_id = l.entity_id
        LEFT JOIN civix.generation_run gr ON el.generation_run_id = gr.run_id
        WHERE el.case_id = :cid
    """
    params: Dict[str, Any] = {"cid": str(case_id), "limit": limit}

    if event_type:
        sql += " AND e.event_type = :event_type"
        params["event_type"] = event_type

    if bbox_coords:
        min_lon, min_lat, max_lon, max_lat = bbox_coords
        sql += " AND l.geometry && ST_MakeEnvelope(:min_lon, :min_lat, :max_lon, :max_lat, 4326)"
        params.update({"min_lon": min_lon, "min_lat": min_lat, "max_lon": max_lon, "max_lat": max_lat})

    sql += " ORDER BY lower(e.occurred_at) ASC LIMIT :limit"

    result = await session.execute(text(sql), params)
    rows = result.fetchall()

    features = []
    for r in rows:
        (el_id, ev_id, ev_type, ev_start, ev_end, is_open, loc_id, loc_name, 
         loc_type, pred, epistemic, cid, src_id, gen_id, gen_origin, geom_json_str) = r

        geometry_obj = json.loads(geom_json_str)
        
        features.append({
            "type": "Feature",
            "geometry": geometry_obj,
            "properties": {
                "event_location_id": el_id,
                "event_id": ev_id,
                "event_type": ev_type,
                "event_start": ev_start,
                "event_end": ev_end,
                "is_open_ended": bool(is_open) if is_open is not None else False,
                "location_id": loc_id,
                "location_name": loc_name,
                "location_type": loc_type,
                "location_predicate": pred,
                "epistemic_status": epistemic,
                "case_id": cid,
                "source_record_id": src_id,
                "generation_run_id": gen_id,
                "generation_origin": gen_origin
            }
        })

    return {
        "type": "FeatureCollection",
        "features": features
    }
