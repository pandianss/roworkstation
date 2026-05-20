from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel

from src.application.services.static_content_service import StaticContentService
from src.core.config.config_loader import get_app_settings

router = APIRouter()
_svc = StaticContentService()


# ── Auth dependency ──────────────────────────────────────────────────────────

def _require_admin(x_admin_password: str = Header(default="")) -> None:
    """Validates the X-Admin-Password header against the configured admin password."""
    settings = get_app_settings()
    if x_admin_password != settings.admin_password:
        raise HTTPException(status_code=401, detail="Invalid admin password.")


# ── Pydantic models ──────────────────────────────────────────────────────────

class ClusterItem(BaseModel):
    id: str
    district: str
    name: str
    icon: str = "🏭"
    description: str = ""
    key_products: list[str] = []
    employment: str = ""
    annual_turnover: str = ""


class PlaceItem(BaseModel):
    id: str
    district: str
    name: str
    icon: str = "📍"
    category: str = ""
    description: str = ""
    best_time: str = ""
    entry: str = "Free"


class ContentPayload(BaseModel):
    business_clusters: list[ClusterItem]
    places: list[PlaceItem]


# ── Public GET ───────────────────────────────────────────────────────────────

@router.get("")
def get_static_content():
    """Return all static content (business clusters + places to visit)."""
    try:
        return _svc.get_all()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/clusters")
def get_clusters():
    """Return business cluster entries."""
    try:
        return {"business_clusters": _svc.get_clusters()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/places")
def get_places():
    """Return places-to-visit entries."""
    try:
        return {"places": _svc.get_places()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── Admin PUT ────────────────────────────────────────────────────────────────

@router.put("", dependencies=[Depends(_require_admin)])
def save_content(payload: ContentPayload):
    """[Admin] Replace the full static content payload."""
    try:
        _svc.save_all(
            business_clusters=[c.model_dump() for c in payload.business_clusters],
            places=[p.model_dump() for p in payload.places],
        )
        return {"status": "ok", "message": "Static content updated successfully."}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.put("/clusters", dependencies=[Depends(_require_admin)])
def save_clusters(clusters: list[ClusterItem]):
    """[Admin] Replace the business clusters list."""
    try:
        _svc.save_clusters([c.model_dump() for c in clusters])
        return {"status": "ok", "message": "Business clusters updated."}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.put("/places", dependencies=[Depends(_require_admin)])
def save_places(places: list[PlaceItem]):
    """[Admin] Replace the places-to-visit list."""
    try:
        _svc.save_places([p.model_dump() for p in places])
        return {"status": "ok", "message": "Places updated."}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
