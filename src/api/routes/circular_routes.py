from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.application.services.circular_service import CircularService

router = APIRouter()


@router.get("")
def get_circulars():
    """Return all published circulars/notices, sorted newest-first."""
    try:
        svc = CircularService()
        circulars = svc.get_all()
        return {"circulars": circulars}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
