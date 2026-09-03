from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

# ------------------------------------------------------------------
# CCTV Source
# ------------------------------------------------------------------
class CCTVSourceBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    source_name: str
    operator_name: str
    website_url: Optional[str] = None
    source_type: str
    verification_status: str

class CCTVSourceResponse(CCTVSourceBase):
    source_id: UUID
    created_at: datetime

class CCTVSourceCreate(BaseModel):
    source_name: str
    operator_name: str
    website_url: Optional[str] = None
    source_type: str = "PUBLIC_MUNICIPAL"
    verification_status: str = "UNVERIFIED"

# ------------------------------------------------------------------
# CCTV Camera
# ------------------------------------------------------------------
class CCTVCameraBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    camera_code: str
    display_name: str
    city: str
    region: str
    latitude: float
    longitude: float
    camera_type: str
    status: str
    access_type: str

class CCTVCameraResponse(CCTVCameraBase):
    camera_id: UUID
    source_id: UUID
    last_health_check: Optional[datetime] = None
    created_at: datetime

class CCTVCameraCreate(CCTVCameraBase):
    source_id: UUID

# ------------------------------------------------------------------
# CCTV Feed
# ------------------------------------------------------------------
class CCTVFeedBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    feed_type: str
    feed_url: str
    embed_url: Optional[str] = None
    frame_rate: int = 15
    resolution_w: int = 1920
    resolution_h: int = 1080
    is_active: bool = True

class CCTVFeedResponse(CCTVFeedBase):
    feed_id: UUID
    camera_id: UUID
    created_at: datetime

class CCTVFeedCreate(CCTVFeedBase):
    camera_id: UUID

# ------------------------------------------------------------------
# CCTV Search Job
# ------------------------------------------------------------------
class CCTVSearchJobRequest(BaseModel):
    case_id: UUID
    target_vehicle_id: Optional[UUID] = None
    camera_ids: List[UUID]
    start_time: datetime
    end_time: datetime

class CCTVSearchJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    job_id: UUID
    case_id: UUID
    requested_by: UUID
    target_vehicle_id: UUID
    camera_ids: List[UUID]
    start_time: datetime
    end_time: datetime
    status: str
    progress_pct: int
    frames_processed: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# ------------------------------------------------------------------
# CCTV Detection & Tracks (For Review)
# ------------------------------------------------------------------
class CCTVMatchCandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    candidate_id: UUID
    job_id: UUID
    track_id: UUID
    case_id: UUID
    target_vehicle_id: UUID
    signal_class: str
    overall_signal: str
    plate_match_type: str
    plate_confidence: Optional[float] = None
    make_match: bool
    model_match: bool
    color_match: bool
    body_match: bool
    visual_similarity_score: Optional[float] = None
    explanation_notes: str
    review_status: str
    created_at: datetime

class CCTVReviewDecision(BaseModel):
    decision: str  # "ACCEPTED" or "REJECTED"
    investigator_notes: Optional[str] = None

class CVTrackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    track_id: UUID
    job_id: UUID
    camera_id: UUID
    track_uuid: str
    first_seen: datetime
    last_seen: datetime
    crop_storage_uri: Optional[str] = None
    detected_make: Optional[str] = None
    created_at: datetime

class CCTVPlateDetectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    plate_detection_id: UUID
    job_id: UUID
    camera_id: UUID
    track_id: UUID
    detection_id: Optional[UUID] = None
    frame_timestamp: datetime
    bounding_box: Any
    plate_crop_storage_uri: str
    raw_ocr_text: str
    normalized_plate: str
    ocr_confidence: float
    confidence_category: str
    detector_model: str
    ocr_engine: str
    ocr_engine_version: str
    created_at: datetime

