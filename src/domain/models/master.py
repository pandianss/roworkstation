from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import uuid

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

class MasterRecord(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    category: str
    code: str
    name_en: str
    name_hi: Optional[str] = None
    name_local: Optional[str] = None
    is_active: bool = True
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
