from __future__ import annotations

from pydantic import BaseModel, Field


class UserAccess(BaseModel):
    username: str
    role: str = "USER"
    dept: str = "ALL"
    depts: list[str] = Field(default_factory=lambda: ["ALL"])
    name: str | None = None
    assigned_branches: list[str] = Field(default_factory=list)
    designation: str | None = None
    grade: str | None = None
    rank: int = 4
