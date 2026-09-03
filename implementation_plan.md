# CIVIX 2.0 CCTV ARCHITECTURE AUDIT

## 1. Executive Verdict

> [!TIP]
> **VERDICT: GO WITH CONDITIONS**

The CCTV Intelligence Subsystem is highly feasible as an additive extension to CIVIX 2.0, provided it strictly adheres to a **PostgreSQL-first, async-job, bounded-projection** architecture.

**The Conditions:**
1. **No Raw Detections in Neo4j:** The outbox/Neo4j projection must ONLY receive investigator-confirmed `cctv_observation` records. Raw YOLO detections/tracks must remain isolated in PostgreSQL to prevent catastrophic graph explosion and outbox queue saturation.
2. **Asynchronous Architecture:** FastAPI cannot synchronously process HLS/RTSP video. All CV workloads must be pushed to a bounded background queue (e.g., Celery/Redis or isolated worker pool).
3. **Semantic Isolation:** The C3 Intelligence Engine and XGBoost behavioral model must NOT ingest raw CV confidence scores. CCTV must only feed C3 through deterministic, provenance-backed facts resulting from investigator review.
4. **Authorized Context:** Every camera search must execute strictly within the RLS boundary of an authorized `case_id`.

## 2. Current Architecture Snapshot

The current CIVIX 2.0 architecture is a highly decoupled intelligence workstation:
*   **Database:** PostgreSQL (`civix_test`) with strict Row-Level Security (RLS) enforcing case access via JWT claims.
*   **Graph Engine:** Neo4j holding a projected, semantic investigation graph.
*   **Synchronization:** PostgreSQL outbox pattern + Change Data Capture (CDC) worker projecting facts to Neo4j.
*   **Intelligence:** Isolated ML service (XGBoost) for behavioral scoring + Gemini for NLP extraction (C3 pipeline).
*   **Frontend:** React + Vite SPA, TanStack Query, Cytoscape.js graph.

## 3. CCTV Capability Mapping

| Capability | Status | Risk | Recommendation |
| :--- | :--- | :--- | :--- |
| **Camera Registry** | Missing | Low | Add `cctv_camera` and `cctv_feed` tables to PostgreSQL. |
| **Global Map** | Missing | Low | Integrate MapLibre GL JS or React-Leaflet on frontend. |
| **Live Grid** | Missing | Medium | Implement lazy-loaded HLS/WebRTC components. Bound concurrent streams to max 4 to prevent browser CPU exhaustion. |
| **Vehicle Search** | Missing | High | Requires async background task. Do not run in FastAPI request cycle. |
| **YOLO / CV** | Missing | High | Use YOLOv8 (ultralytics) for object detection. Local inference using PyTorch. |
| **Tracking** | Missing | Medium | Implement ByteTrack or BoT-SORT to aggregate frames into `cctv_track`. |
| **ANPR / OCR** | Missing | High | PaddleOCR or EasyOCR for Indian plates, tied to the track lifecycle to vote on the best plate candidate. |
| **Matching Logic** | Missing | Medium | Implement deterministic signal matrix (Plate, Make/Model, Color). |
| **Observations** | Missing | Low | Add `cctv_observation` table linked to existing `evidence_instance`. |
| **Graph Projection** | Existing (Neo4j) | CRITICAL | ONLY project reviewed `cctv_observation` records. Do NOT project `cctv_detection`. |

## 4. Blast Radius

*   **Neo4j Graph Database:** **CRITICAL**. If raw detections enter the CDC outbox, they will flood Neo4j with millions of useless "Vehicle" nodes and crash the CDC worker.
*   **PostgreSQL Performance:** **HIGH**. Constant writing of high-frequency ML detections could cause lock contention or exhaust connections. Requires batch-inserts and isolated tables.
*   **FastAPI Backend:** **HIGH**. Video transcoding/processing inside ASGI workers will block the event loop and crash the API.
*   **RLS/Auth:** **MEDIUM**. Needs careful integration to ensure users cannot view cameras/detections for cases they don't own.
*   **Frontend:** **LOW**. Additive route (`/cctv`).

## 5. Database Architecture

**Proposed Additive Tables (PostgreSQL):**

1.  **`cctv_camera`**: Public registry (ID, Name, Location/Geometry, Region, Status).
2.  **`cctv_feed`**: Technical connection info (URL, Type: HLS/RTSP/MJPEG).
3.  **`cctv_search_job`**: Async task state (Case ID, Target Vehicle, Status, Started/Ended).
4.  **`cctv_track`**: Aggregated vehicle track over time (Job ID, Camera ID, Start/End Time, Best Plate, Best Make/Model).
5.  **`cctv_observation`**: The human-reviewed result. Foreign keys to `cctv_track`, `case_id`, `investigator_id`.

*All tables will enforce `civix.current_user_id` RLS through `case_id` or global public read access (for camera registry).*

## 6. PostgreSQL vs Neo4j Boundary

> [!WARNING]
> **The Boundary is Human Review.**

*   **PostgreSQL Only:** `cctv_camera`, `cctv_feed`, `cctv_search_job`, `cctv_track`.
*   **Neo4j Projected:** `cctv_observation` ONLY.
When an investigator clicks "Accept" on a match, a `cctv_observation` is created. This observation acts as a factual `assertion` or `evidence_instance` and is projected to Neo4j as:
`(InvestigativeCase)-[:HAS_OBSERVATION]->(CCTVObservation)-[:IDENTIFIES]->(Vehicle)`

## 7. CDC / Outbox Decision

**CCTV MUST use the CDC Outbox, but strictly filtered.**
*   Do NOT emit outbox events for `cctv_track` or `cctv_search_job`.
*   Only emit `CCTV_OBSERVATION_CREATED`.
*   This protects the CDC pipeline (C1 semantics) from video-framerate queue saturation.

## 8. CV Architecture

*   **Detector:** YOLOv8 (nano or small) for high-FPS CPU/mid-GPU inference.
*   **Tracker:** ByteTrack (lightweight, associates boxes across frames).
*   **OCR:** PaddleOCR (better out-of-the-box text recognition for difficult plates than EasyOCR).
*   **Vehicle Classifier:** A secondary lightweight ResNet/MobileNet classifier cropped on the vehicle bounding box to predict Make/Model/Color.
*   **Matching Engine:** Deterministic rule-based matrix. `Plate Match = EXACT` trumps all. If plate is unreadable, `Model + Color + Time = MODERATE POTENTIAL`.

## 9. Video Architecture

*   **Browser:** Direct HLS/WebRTC playback where possible. Avoid proxying video through FastAPI.
*   **Backend CV Ingestion:** OpenCV `VideoCapture` utilizing `ffmpeg` backend to sample streams at 2-5 FPS (we do not need 30 FPS for investigative vehicle matching).

## 10. Async Job Architecture

FastAPI creates a `cctv_search_job` in PostgreSQL and returns `202 Accepted` with a Job ID.
A dedicated Python worker (e.g., Celery, or a simple asyncio loop listening to a PostgreSQL `LISTEN/NOTIFY` or Redis queue) picks up the job, connects to the stream, runs YOLO/Tracking, writes `cctv_track` rows, and marks the job `COMPLETED`. The frontend polls or uses SSE to watch the Job ID status.

## 11. Case Integration

CCTV Search is launched **from within a Case Context**.
1. Frontend calls `/api/v1/cases/{case_id}/vehicles` to get known case vehicles.
2. User selects a vehicle and clicks "Search Cameras".
3. Payload sent: `{ case_id, target_entity_id, camera_ids, time_window }`.
4. RLS guarantees the user has `case_access`.

## 12. Vehicle Matching Algorithm

CIVIX must preserve epistemological uncertainty:
*   **EXACT_PLATE:** OCR exactly matches case vehicle plate. (Signal: **HIGH**)
*   **PARTIAL_PLATE:** OCR matches 4+ characters, Make/Model matches. (Signal: **HIGH**)
*   **ATTRIBUTE_MATCH:** Plate unreadable, but Make, Model, Color match precisely. (Signal: **MODERATE**)
*   **VISUAL_SIMILARITY:** Make/Color match, but low confidence. (Signal: **LOW**)

## 13. Security

*   **SSRF Mitigation:** The backend CV worker must ONLY connect to feeds registered in `cctv_feed` by administrators. It must strictly reject arbitrary URLs supplied by the frontend payload.
*   **Path Traversal:** Video crops/evidence must be stored using cryptographically secure UUID filenames in the existing `civix_evidence_store`.
*   **Auth Bypass:** RLS must apply to `cctv_search_job`.

## 14. RLS Integration

```sql
CREATE POLICY cctv_search_job_access ON civix.cctv_search_job
FOR ALL USING (
  EXISTS (
    SELECT 1 FROM civix.case_access ca
    WHERE ca.case_id = cctv_search_job.case_id
    AND ca.user_id = current_setting('civix.current_user_id')::uuid
    AND ca.is_revoked = false
  )
);
```

## 15. Storage

*   **DO NOT** store full video streams.
*   **DO** store cropped JPEGs of the vehicle and the license plate upon a successful `cctv_track` completion. Upload to existing `evidence_artifact` table with a `sha256_hash`.

## 16. Frontend Architecture

*   `frontend/src/pages/CCTVCommandCenterPage.tsx`
*   `frontend/src/components/cctv/CameraMap.tsx` (Leaflet)
*   `frontend/src/components/cctv/CameraGrid.tsx`
*   `frontend/src/components/cctv/ObservationReviewPanel.tsx`
*   `frontend/src/api/cctv.ts`

## 17. External Camera Source Architecture

Public feeds (Traffic cams, Transport APIs) are seeded via `civix_generator` into `cctv_camera`. A background cron job pings feeds every 10 minutes to update `status='ONLINE' | 'OFFLINE'`.

## 18. Performance Budget

*   **Max Concurrent Streams in UI:** 4.
*   **Max Concurrent CV Jobs:** 2 per GPU/Worker.
*   **Inference FPS:** Sample at 3 FPS.
*   **Max Search Duration:** 15 minutes of historical video (or 15 mins of live watching) per job.

## 19. Failure Containment

If the CV worker crashes (OOM, invalid HLS), the `cctv_search_job` errors out safely in PostgreSQL. The frontend displays "Job Failed". It does NOT crash the FastAPI backend, Neo4j, or the CDC outbox.

## 20. Testing Strategy

*   **Fixtures:** We need 3 short (5-second) `.mp4` test videos stored in a `civix_golden_evidence/cctv` directory.
    *   `video_exact_match.mp4` (Clear plate)
    *   `video_attribute_match.mp4` (Blurry plate, matching car)
    *   `video_negative.mp4` (Different car)
*   **E2E Test:** Spin up worker, mock the camera feed with the local `.mp4`, assert `cctv_track` results.

## 21. Migration Plan

1. Create additive `cctv_*` tables.
2. Add RLS policies identical to `case_access` patterns.
3. Deploy CV Worker logic.
4. Add FastAPI `/cctv` router.
5. Deploy React Frontend `/cctv` route.

## 22. Implementation Phases

*   **Phase A:** Additive schema migrations & Camera Registry.
*   **Phase B:** Map & Live UI Grid (Frontend).
*   **Phase C:** CV Background Worker & Mock Video ingestion.
*   **Phase D:** Async Search Job API & Case Integration.
*   **Phase E:** Analyst Review UI & Outbox Projection.

## 23. Files That Would Need To Change

**NEW FILES:**
*   `civix_api/routers/cctv.py`
*   `civix_api/models/cctv.py`
*   `civix_api/worker/cctv_processor.py`
*   `database/migrations/V008__cctv_schema.sql`
*   `frontend/src/pages/CCTVCommandCenterPage.tsx`
*   `frontend/src/api/cctv.ts`

**MODIFIED FILES:**
*   `civix_api/main.py` (Include new router)
*   `civix_api/services/neo4j_projection.py` (Add projection logic for `cctv_observation`)
*   `frontend/src/router/AppRouter.tsx`
*   `frontend/src/components/layouts/AppSidebar.tsx`

**FILES THAT MUST NOT BE TOUCHED:**
*   `civix_api/services/intelligence_engine.py` (C3 is frozen)
*   `database/migrations/V001` - `V007`

## 24. Dependency Changes

*   **Backend:** `ultralytics` (YOLOv8), `paddleocr`, `opencv-python-headless`. (High Risk: Dependency bloat. Mitigation: Isolate in a separate worker Dockerfile if possible).
*   **Frontend:** `leaflet`, `react-leaflet` (Low risk).

## 25. Regression Protection

*   C0 evidence ingestion must remain untouched.
*   C1 CDC outbox consumption tests MUST pass (CCTV must not poison the DLQ).
*   C2 identity resolution must NOT trigger automatically from CCTV.
*   C3 feature vectors must remain completely unaware of raw CCTV tracks.

## 26. Dangerous Approaches Rejected

*   **REJECTED:** Storing every vehicle bounding box as a Neo4j Node. (Causes instant graph database saturation).
*   **REJECTED:** Running YOLO directly inside a FastAPI route. (Blocks ASGI event loop, causes total API outage).
*   **REJECTED:** Frontend providing arbitrary stream URLs. (Massive SSRF vulnerability).
*   **REJECTED:** C3 XGBoost model taking CV confidence scores as features. (Corrupts the frozen 70-feature contract).

## 27. Implementation Readiness Checklist

- [ ] New `cctv_` tables schema reviewed for isolated FKs.
- [ ] RLS policies confirmed mirroring `case_access`.
- [ ] Background CV worker architecture selected (Celery vs native Asyncio Queue).
- [ ] Sample 5-second fixture `.mp4` videos acquired for deterministic testing.
- [ ] Outbox projection logic strictly gated behind `cctv_observation`.

## 28. Final Recommendation

**Can we implement this safely?** Yes, because the PostgreSQL `cctv_*` tables and background worker are completely orthogonal to existing C0-C4 structures.

**What is the safest MVP?** A camera registry UI (Phase A+B), followed by async video search against known local `.mp4` fixtures (Phase C+D).

**What must NOT be attempted yet?** Live streaming of hundreds of cameras into C3 intelligence layers. Maintain the "Human Review" airgap forever.
