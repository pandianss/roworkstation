from __future__ import annotations

import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from src.application.services.anniversary_service import AnniversaryService
from src.application.services.master_data_service import MasterDataService

router = APIRouter()


def _serialize_dates(records: list) -> list:
    """Convert date/datetime fields to ISO strings in a list of dicts."""
    result = []
    for item in records:
        row = {}
        for k, v in item.items():
            if isinstance(v, (datetime.date, datetime.datetime)):
                row[k] = v.isoformat()
            else:
                row[k] = v
        result.append(row)
    return result


@router.get("/branches")
def get_branch_anniversaries(
    days: int = Query(30, description="Look-ahead window in days", ge=1, le=365),
):
    """
    Upcoming branch anniversary milestones within the next N days.
    Returns: {anniversaries: list}
    """
    try:
        svc = AnniversaryService()
        anniversaries = svc.get_upcoming_anniversaries(days=days)
        return {"anniversaries": _serialize_dates(anniversaries)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/staff")
def get_staff_celebrations(
    days: int = Query(15, description="Look-ahead window in days", ge=1, le=365),
):
    """
    Upcoming staff celebrations (birthdays, retirements) within the next N days.
    Returns: {celebrations: list}
    """
    try:
        svc = AnniversaryService()
        celebrations = svc.get_staff_celebrations(days=days)
        return {"celebrations": _serialize_dates(celebrations)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/registry")
def get_branch_registry():
    """
    All branches with founding / opening dates populated.
    Returns: {branches: list} with Code, Name, Open Date, District, Type columns.
    """
    try:
        import math

        svc = MasterDataService()
        df = svc.get_units_frame()

        if df.empty:
            return {"branches": []}

        # Keep only rows where Open Date is actually set
        df = df[df["Open Date"].notna()]

        # Convert datetime columns to ISO strings
        for col in df.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns:
            df[col] = df[col].dt.strftime("%Y-%m-%d").where(df[col].notna(), None)

        # Select relevant columns
        keep = [c for c in ["Code", "Name", "Open Date", "District", "Type"] if c in df.columns]
        df = df[keep]

        # Clean NaN / Inf floats
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

        return {"branches": cleaned}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
