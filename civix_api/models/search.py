from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from uuid import UUID

class SearchResult(BaseModel):
    entity_id: UUID
    entity_type: str
    display_label: str
    matched_field: str

    model_config = ConfigDict(from_attributes=True)

class SearchResponse(BaseModel):
    results: List[SearchResult]
    limit: int
    offset: int
