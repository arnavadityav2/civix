import os
import sys
import pytest
import psycopg
from unittest.mock import MagicMock

from civix_api.worker.cctv_worker import CCTVWorker
from civix_api.services.cv.base import CVDetection, CVTrack

TEST_DSN = os.getenv("CIVIX_DATABASE_URL", "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test").replace("+asyncpg", "")

@pytest.fixture
def clean_db():
    pass

def test_phase_b_provenance_and_boundaries(monkeypatch):
    worker = CCTVWorker(pg_dsn="postgresql://mock")
    
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_connect = MagicMock()
    mock_connect.return_value.__enter__.return_value = mock_conn
    monkeypatch.setattr("psycopg.connect", mock_connect)
    
    # Mock the job query to return 1 job
    mock_cur.fetchone.side_effect = [
        ("job-1", "case-1", "veh-1", ["cam-1"]), # Job fetch
        ("file://tests/fixtures/cctv/mock_traffic.mp4",) # Feed fetch
    ]
    
    mock_processor = MagicMock()
    mock_processor.process_video.return_value = (
        [CVDetection(frame_number=1, bounding_box=(0,0,10,10), object_class="car", confidence=0.9)],
        [CVTrack(track_id="trk-1", first_frame=1, last_frame=2, detections=[], object_class="car", confidence=0.9, best_crop=MagicMock())]
    )
    worker.video_processor = mock_processor
    
    worker.artifact_manager = MagicMock()
    worker.artifact_manager.save_track_crop.return_value = "local://cctv_crops/mock.jpg"
    
    processed = worker.process_next_job()
    assert processed is True
    
    # Assert constraints:
    queries = [call[0][0] for call in mock_cur.execute.call_args_list]
    
    # 1. Should insert detection
    assert any("INSERT INTO civix.cctv_detection" in q for q in queries)
    # 2. Should insert track
    assert any("INSERT INTO civix.cctv_track" in q for q in queries)
    # 3. Should update job status
    assert any("UPDATE civix.cctv_search_job SET status = 'COMPLETED'" in q for q in queries)
    
    # Phase B Constraints: MUST NOT CREATE Candidates or Observations
    assert not any("civix.cctv_match_candidate" in q for q in queries)
    assert not any("civix.cctv_observation" in q for q in queries)

