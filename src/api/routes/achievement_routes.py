from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.application.services.achievement_service import AchievementService

router = APIRouter()


@router.get("")
def get_achievements():
    """Return all published regional achievements."""
    try:
        svc = AchievementService()
        achievements = svc.get_all()
        return {"achievements": achievements}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
