from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class RegistrySource(BaseModel):
    source_name: str
    operator_name: str
    website_url: Optional[str]
    source_type: str
    verification_status: str

class RegistryCamera(BaseModel):
    camera_code: str
    display_name: str
    city: str
    region: str
    latitude: float
    longitude: float
    camera_type: str
    status: str
    access_type: str
    feed_type: str
    feed_url: str
    embed_url: Optional[str] = None
    frame_rate: int = 15

class BaseCameraProvider(ABC):
    @abstractmethod
    def get_source_metadata(self) -> RegistrySource:
        """Return metadata about this source."""
        pass

    @abstractmethod
    def fetch_cameras(self) -> List[RegistryCamera]:
        """Fetch and normalize all available cameras from this provider."""
        pass
