from __future__ import annotations

import math
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from src.application.services.guardian_service import GuardianService

router = APIRouter()


def _serialize_followup(f) -> dict:
    """Convert a GuardianFollowUp Pydantic model to a JSON-safe dict."""
    d = f.model_dump()
    # Serialize timestamp to string
    ts = d.get("timestamp")
    if hasattr(ts, "isoformat"):
        d["timestamp"] = ts.isoformat()
    elif ts is not None:
        d["timestamp"] = str(ts)
    return d


def _clean_portfolio_row(row: dict) -> dict:
    """Replace NaN / Inf floats in a portfolio row with None."""
    return {
        k: (None if isinstance(v, float) and (math.isnan(v) or math.isinf(v)) else v)
        for k, v in row.items()
    }


@router.get("/followups")
def get_followups():
    """
    All active follow-up observations recorded by Guardian Officers.
    Returns: {followups: list}
    """
    try:
        svc = GuardianService()
        followups = svc.list_followups()
        return {"followups": [_serialize_followup(f) for f in followups]}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/portfolio")
def get_portfolio(
    sols: Optional[str] = Query(
        None, description="Comma-separated SOL codes, e.g. 2706,1234"
    ),
):
    """
    Portfolio MIS metrics for a specific set of branch SOLs.
    Returns: {portfolio: list}
    """
    try:
        sol_list = (
            [s.strip() for s in sols.split(",") if s.strip()]
            if sols
            else []
        )

        svc = GuardianService()
        portfolio = svc.get_portfolio_mis(sol_list)
        cleaned = [_clean_portfolio_row(row) for row in portfolio]
        return {"portfolio": cleaned}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
