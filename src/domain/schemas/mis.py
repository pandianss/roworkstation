from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class MISFilter(BaseModel):
    selected_date: date | None = None
    sols: list[int] = Field(default_factory=list)


class MISSnapshot(BaseModel):
    selected_date: date
    available_dates: list[date]
    available_sols: list[int]
    kpis: dict[str, float]
    rows: list[dict]
    history_rows: list[dict]
    milestones: list[dict] | None = None
    milestone_breakthroughs: list[dict] | None = None

