from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.application.services.campaign_service import CampaignService

router = APIRouter()


@router.get("")
def get_campaigns():
    """Return all campaigns (active and completed)."""
    try:
        svc = CampaignService()
        campaigns = svc.get_all()
        return {"campaigns": campaigns}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
