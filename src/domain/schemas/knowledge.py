from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class IndexedDocument(BaseModel):
    file_name: str
    department: str
    uploaded_by: str
    chunks: int
    indexed_at: datetime
