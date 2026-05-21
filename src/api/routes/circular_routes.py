from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

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


@router.get("/search")
def search_circulars(
    q: Optional[str] = Query(None, description="Search term matched against subject and ref_no"),
    dept: Optional[str] = Query(None, description="Department code/name filter"),
    limit: int = Query(50, description="Maximum number of results to return", ge=1, le=500),
):
    """
    Filtered circular search with optional keyword and department filtering.
    Returns: {circulars: list, total: int}
    """
    try:
        svc = CircularService()
        all_circulars = svc.get_all()

        results = all_circulars

        # Keyword filter — searches subject and ref_no fields
        if q:
            q_lower = q.lower()
            results = [
                c for c in results
                if (
                    q_lower in str(c.get("subject", "")).lower()
                    or q_lower in str(c.get("ref_no", "")).lower()
                    or q_lower in str(c.get("number", "")).lower()
                )
            ]

        # Department filter
        if dept:
            dept_lower = dept.lower()
            results = [
                c for c in results
                if dept_lower in str(c.get("dept", "")).lower()
            ]

        total = len(results)
        paginated = results[:limit]

        return {"circulars": paginated, "total": total}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
