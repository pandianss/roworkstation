from __future__ import annotations

import math
from fastapi import APIRouter, HTTPException

from src.application.services.master_data_service import MasterDataService

router = APIRouter()
_data_svc = MasterDataService()


def _safe_serialize(df):
    """Convert DataFrame to JSON-safe list of dicts (handles NaT/NaN/Inf)."""
    import pandas as pd

    for col in df.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns:
        df[col] = df[col].dt.strftime("%Y-%m-%d").where(df[col].notna(), None)

    records = df.to_dict(orient="records")
    cleaned = []
    for row in records:
        cleaned_row = {}
        for k, v in row.items():
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                cleaned_row[k] = None
            else:
                cleaned_row[k] = v
        cleaned.append(cleaned_row)
    return cleaned


@router.get("/units")
def get_units():
    """
    Return all branch units with name, type, district, population group,
    head/2nd-line officer names, open date, and active status.
    """
    try:
        df = _data_svc.get_units_frame()
        if df.empty:
            return {"units": []}
        return {"units": _safe_serialize(df)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/departments")
def get_departments():
    """Return all regional office departments (active only)."""
    try:
        df = _data_svc.get_departments_frame()
        if df.empty:
            return {"departments": []}
        return {"departments": _safe_serialize(df)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/staff")
def get_staff():
    """Return the full staff roster from master data."""
    try:
        df = _data_svc.get_staff_frame()
        if df.empty:
            return {"staff": []}
        return {"staff": _safe_serialize(df)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
