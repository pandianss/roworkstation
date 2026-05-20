from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from src.domain.models.enums import TaskPriority


class TaskCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    title: str
    dept: str
    assigned_to: str
    priority: TaskPriority = TaskPriority.P3
    due_date: date | None = None
    task_type: str = "PERSONAL"
    source: str = "user"
    description: str = ""


class TaskRead(TaskCreate):
    id: str
    status: str = "OPEN"
    assigned_by: str | None = None
    created_at: datetime | None = None
