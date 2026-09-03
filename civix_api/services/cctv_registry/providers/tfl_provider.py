import requests
import logging
from typing import List
from ..base_provider import BaseCameraProvider, RegistrySource, RegistryCamera

logger = logging.getLogger(__name__)

class TFLCameraProvider(BaseCameraProvider):
    """
    Provider for Transport for London (TfL) JamCams.
    Official public data source for London traffic cameras.
    """
    API_URL = "https://api.tfl.gov.uk/Place/Type/JamCam"

    def get_source_metadata(self) -> RegistrySource:
        return RegistrySource(
            source_name="TfL JamCams",
            operator_name="Transport for London",
            website_url="https://tfl.gov.uk/info-for/open-data-users/our-open-data",
            source_type="PUBLIC_TRANSIT",
            verification_status="VERIFIED"
        )

    def fetch_cameras(self, limit: int = 50) -> List[RegistryCamera]:
        logger.info("Fetching JamCams from TfL Open Data API...")
        try:
            response = requests.get(self.API_URL, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.error(f"Failed to fetch TfL JamCams: {e}")
            return []

        cameras = []
        for place in data[:limit]:
            camera_code = place.get('id', '')
            display_name = place.get('commonName', camera_code)
            lat = place.get('lat', 0.0)
            lon = place.get('lon', 0.0)
            
            # Extract video URL from additional properties
            properties = {p['key']: p['value'] for p in place.get('additionalProperties', [])}
            feed_url = properties.get('videoUrl', '')
            if not feed_url:
                feed_url = properties.get('imageUrl', '')
            
            feed_type = 'RTSP' if 'rtsp' in feed_url.lower() else 'MJPEG' if '.mjpg' in feed_url.lower() else 'SNAPSHOT_POLL'
            
            cameras.append(RegistryCamera(
                camera_code=camera_code,
                display_name=display_name,
                city="London",
                region="Greater London",
                latitude=lat,
                longitude=lon,
                camera_type="FIXED_TRAFFIC",
                status="REGISTERED_ONLY", # Will be updated during verification
                access_type="PUBLIC_LIVE",
                feed_type=feed_type,
                feed_url=feed_url
            ))
            
        logger.info(f"Normalized {len(cameras)} TfL JamCams.")
        return cameras
