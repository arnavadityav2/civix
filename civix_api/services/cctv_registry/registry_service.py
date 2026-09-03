import os
import urllib.parse
import ipaddress
import socket
import logging
import psycopg
from typing import List, Tuple
from datetime import datetime

from .base_provider import BaseCameraProvider
from .providers.tfl_provider import TFLCameraProvider
from .providers.delhi_ncr_provider import DelhiNCRProvider

logger = logging.getLogger(__name__)

class SecurityException(Exception):
    pass

class CameraRegistryService:
    def __init__(self, pg_dsn: str = None):
        self.pg_dsn = pg_dsn or os.getenv("CIVIX_DATABASE_URL", "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test").replace("+asyncpg", "")
        self.providers: List[BaseCameraProvider] = [
            DelhiNCRProvider(),
            TFLCameraProvider()
        ]

    def validate_url_security(self, url: str) -> bool:
        """
        SSRF Protection: Validates that the URL resolves to a public routable IP
        and does not target private or local networks.
        """
        if not url:
            return False
            
        try:
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme not in ('http', 'https', 'rtsp'):
                return False
                
            hostname = parsed.hostname
            if not hostname:
                return False
                
            # Block obvious local hosts
            if hostname.lower() in ('localhost', '127.0.0.1', '::1'):
                return False
                
            # Resolve IP and check if it's public
            # Note: in a production async environment, this blocking DNS resolution 
            # should be done via aiodns.
            ip = socket.gethostbyname(hostname)
            ip_obj = ipaddress.ip_address(ip)
            
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_multicast:
                logger.warning(f"SSRF Blocked: URL {url} resolved to private/local IP {ip}")
                return False
                
            return True
        except Exception as e:
            logger.error(f"URL security validation failed for {url}: {e}")
            return False

    def sync_providers(self) -> dict:
        """
        Iterates through all registered providers, fetches their cameras,
        validates feed URLs, and performs idempotent ingestion into PostgreSQL.
        """
        results = {
            "sources_discovered": len(self.providers),
            "sources_registered": 0,
            "cameras_discovered": 0,
            "cameras_registered": 0,
            "feeds_registered": 0,
            "feeds_rejected_security": 0
        }
        
        with psycopg.connect(self.pg_dsn) as conn:
            with conn.cursor() as cur:
                for provider in self.providers:
                    meta = provider.get_source_metadata()
                    
                    # 1. Register Source (Idempotent)
                    cur.execute("""
                        INSERT INTO civix.cctv_source (source_name, operator_name, website_url, source_type, verification_status)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (source_name) DO UPDATE SET
                            operator_name = EXCLUDED.operator_name,
                            website_url = EXCLUDED.website_url,
                            verification_status = EXCLUDED.verification_status
                        RETURNING source_id
                    """, (meta.source_name, meta.operator_name, meta.website_url, meta.source_type, meta.verification_status))
                    
                    source_id = cur.fetchone()[0]
                    results["sources_registered"] += 1
                    
                    # 2. Fetch Cameras
                    cameras = provider.fetch_cameras()
                    results["cameras_discovered"] += len(cameras)
                    
                    if not cameras:
                        # Log absence (e.g. Delhi NCR)
                        if meta.verification_status == 'UNVERIFIED':
                            cur.execute("""
                                UPDATE civix.cctv_source SET verification_status = 'DEPRECATED'
                                WHERE source_id = %s
                            """, (source_id,))
                        continue
                        
                    # 3. Register Cameras & Feeds
                    for cam in cameras:
                        # Register Camera
                        cur.execute("""
                            INSERT INTO civix.cctv_camera 
                            (source_id, camera_code, display_name, city, region, latitude, longitude, camera_type, status, access_type)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (camera_code) DO UPDATE SET
                                display_name = EXCLUDED.display_name,
                                status = EXCLUDED.status,
                                latitude = EXCLUDED.latitude,
                                longitude = EXCLUDED.longitude
                            RETURNING camera_id
                        """, (source_id, cam.camera_code, cam.display_name, cam.city, cam.region, cam.latitude, cam.longitude, cam.camera_type, cam.status, cam.access_type))
                        
                        camera_id = cur.fetchone()[0]
                        results["cameras_registered"] += 1
                        
                        # Register Feed (after SSRF validation)
                        if self.validate_url_security(cam.feed_url):
                            cur.execute("SELECT feed_id FROM civix.cctv_feed WHERE camera_id = %s", (camera_id,))
                            existing_feed = cur.fetchone()
                            if existing_feed:
                                cur.execute("""
                                    UPDATE civix.cctv_feed SET
                                        feed_url = %s,
                                        embed_url = %s,
                                        is_active = true,
                                        feed_type = %s,
                                        frame_rate = %s
                                    WHERE camera_id = %s
                                """, (cam.feed_url, cam.embed_url, cam.feed_type, cam.frame_rate, camera_id))
                            else:
                                cur.execute("""
                                    INSERT INTO civix.cctv_feed
                                    (camera_id, feed_type, feed_url, embed_url, frame_rate)
                                    VALUES (%s, %s, %s, %s, %s)
                                """, (camera_id, cam.feed_type, cam.feed_url, cam.embed_url, cam.frame_rate))
                            results["feeds_registered"] += 1
                        else:
                            results["feeds_rejected_security"] += 1
                            
            conn.commit()
            
        logger.info(f"Sync complete: {results}")
        return results
