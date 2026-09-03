from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class AuthenticatedCivixUser(BaseModel):
    user_id: UUID
    username: str
    role: str
    clearance_level: str

