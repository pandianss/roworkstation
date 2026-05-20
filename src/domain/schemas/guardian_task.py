from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class GuardianDailyTask(BaseModel):
    id: str
    timestamp: datetime
    date: str
    posted_by: str
    title: str
    description: str
