from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, time, datetime, timezone
import uuid

def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    dept: Optional[str] = None
    task_type: Optional[str] = None
    priority: str = "P3"
    due_date: date
    due_time: Optional[time] = None
    assigned_to: str
    assigned_by: Optional[str] = None
    status: str = "OPEN"
    source: Optional[str] = None
    linked_id: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    snoozed_until: Optional[date] = None
    recurrence: Optional[str] = None

class Reminder(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    remind_at: datetime
    channel: str = "APP"
    sent: bool = False
    acknowledged: bool = False
