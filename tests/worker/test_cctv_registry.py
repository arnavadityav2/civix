import pytest
import os
import psycopg
from civix_api.services.cctv_registry.registry_service import CameraRegistryService

@pytest.fixture
def clean_db():
    dsn = os.getenv("CIVIX_DATABASE_URL", "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test").replace("+asyncpg", "")
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM civix.cctv_source")
            cur.execute("DELETE FROM civix.cctv_camera")
            cur.execute("DELETE FROM civix.cctv_feed")
        conn.commit()
    return dsn

def test_registry_sync_idempotent(clean_db):
    service = CameraRegistryService(pg_dsn=clean_db)
    
    # Run first sync
    results1 = service.sync_providers()
    assert results1["sources_discovered"] == 2
    assert results1["sources_registered"] == 2
    assert results1["cameras_registered"] > 0
    
    initial_cams = results1["cameras_registered"]
    initial_feeds = results1["feeds_registered"]
    
    # Run second sync
    results2 = service.sync_providers()
    
    # Verify idempotency
    with psycopg.connect(clean_db) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM civix.cctv_source")
            sources_count = cur.fetchone()[0]
            assert sources_count == 2
            
            cur.execute("SELECT COUNT(*) FROM civix.cctv_camera")
            cameras_count = cur.fetchone()[0]
            assert cameras_count == initial_cams
            
            cur.execute("SELECT COUNT(*) FROM civix.cctv_feed")
            feeds_count = cur.fetchone()[0]
            assert feeds_count == initial_feeds

def test_ssrf_protection():
    service = CameraRegistryService()
    
    # Valid urls
    assert service.validate_url_security("https://api.tfl.gov.uk/something") == True
    assert service.validate_url_security("rtsp://example.com/feed") == True
    
    # Blocked urls
    assert service.validate_url_security("http://localhost:8080") == False
    assert service.validate_url_security("http://127.0.0.1/feed") == False
    assert service.validate_url_security("http://10.0.0.5/feed") == False
    assert service.validate_url_security("http://192.168.1.100/feed") == False
    assert service.validate_url_security("file:///etc/passwd") == False

def test_delhi_provider(clean_db):
    service = CameraRegistryService(pg_dsn=clean_db)
    
    with psycopg.connect(clean_db) as conn:
        with conn.cursor() as cur:
            # Sync
            service.sync_providers()
            
            cur.execute("SELECT verification_status FROM civix.cctv_source WHERE source_name LIKE '%Delhi%'")
            row = cur.fetchone()
            assert row is not None
            assert row[0] == 'DEPRECATED'
            
            # Ensure no cameras mapped for Delhi
            cur.execute("SELECT COUNT(*) FROM civix.cctv_camera WHERE city = 'Delhi'")
            assert cur.fetchone()[0] == 0
