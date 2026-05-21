from __future__ import annotations

import datetime
import math
from typing import Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from src.application.use_cases.mis.service import MISAnalyticsService

router = APIRouter()

# Single service instance — used for ingestion helpers and available-dates
_mis_service = MISAnalyticsService()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean_value(v):
    """Return None for NaN / Inf floats, otherwise return the value as-is."""
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


def _load_enriched_frame(date_str: Optional[str] = None):
    """
    Load MIS data **directly** from the repository (no Streamlit session_state /
    cache dependencies) and apply lightweight metric enrichment.

    Returns (df_all, df_for_date, selected_date) where df_all is the full frame
    and df_for_date is already filtered to selected_date.
    """
    from src.infrastructure.persistence.mis_repository import MISRepository

    repo = MISRepository()
    available_dates = repo.get_available_dates()
    if not available_dates:
        return None, None, None

    # Resolve selected date
    if date_str:
        try:
            selected_date = datetime.date.fromisoformat(date_str)
        except ValueError:
            raise ValueError(f"Invalid date format: '{date_str}'. Use YYYY-MM-DD.")
    else:
        selected_date = available_dates[-1]

    df = repo.load_frame()
    if df.empty:
        return None, pd.DataFrame(), selected_date

    df.columns = [c.upper().replace("_", " ") for c in df.columns]
    df["DATE"] = pd.to_datetime(df["DATE"])

    # Derived columns
    if "TOTAL DEPOSITS" not in df.columns:
        deps_cols = [c for c in ["SB", "CD", "TD"] if c in df.columns]
        df["TOTAL DEPOSITS"] = df[deps_cols].fillna(0).sum(axis=1) if deps_cols else 0.0
    if "ADV" not in df.columns:
        df["ADV"] = 0.0

    df["CD RATIO"] = np.where(
        df["TOTAL DEPOSITS"] > 0,
        df["ADV"] / df["TOTAL DEPOSITS"] * 100,
        0,
    ).round(2)

    # Exclude RO aggregate SOL to prevent double-counting
    if "SOL" in df.columns:
        df = df[df["SOL"] != 3933]

    df_date = df[df["DATE"].dt.date == selected_date].copy()
    return df, df_date, selected_date


# ---------------------------------------------------------------------------
# Existing endpoints (kept exactly as-is)
# ---------------------------------------------------------------------------

@router.get("/data")
def get_mis_data(
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
    force_ingest: bool = Query(False, description="Force re-ingestion of Excel files before loading"),
):
    """Fetch the complete MIS dataset."""
    try:
        df = _mis_service.get_data(
            force_ingest=force_ingest,
            start_date=start_date,
            end_date=end_date,
        )
        if df.empty:
            return {"data": [], "message": "No data found for the given parameters."}

        df = df.replace([pd.NA, math.nan, float("inf"), float("-inf")], None)
        for col in df.select_dtypes(include=["datetime64[ns]"]).columns:
            df[col] = df[col].dt.strftime("%Y-%m-%d")

        return {"data": df.to_dict(orient="records")}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/available-dates")
def get_available_dates():
    """Get a list of dates for which MIS data is available."""
    try:
        dates = _mis_service.get_available_dates()
        return {"dates": [d.strftime("%Y-%m-%d") for d in dates]}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# New endpoints
# ---------------------------------------------------------------------------

@router.get("/summary")
def get_mis_summary(
    date: Optional[str] = Query(None, description="Reporting date YYYY-MM-DD (defaults to latest)"),
    sols: Optional[str] = Query(None, description="Comma-separated SOL codes, e.g. 2706,1234"),
):
    """
    KPI snapshot for a given date and optional SOL filter.
    Returns: {kpis, selected_date, row_count}
    """
    try:
        sol_list = (
            [int(s.strip()) for s in sols.split(",") if s.strip()]
            if sols
            else None
        )

        df_all, df_date, selected_date = _load_enriched_frame(date)
        if selected_date is None:
            return {"kpis": {}, "selected_date": None, "row_count": 0}

        if df_date is None or df_date.empty:
            return {"kpis": {}, "selected_date": str(selected_date), "row_count": 0}

        if sol_list:
            df_date = df_date[df_date["SOL"].isin(sol_list)]

        total_adv = float(df_date["ADV"].sum()) if "ADV" in df_date.columns else 0.0
        total_npa = float(df_date["NPA"].sum()) if "NPA" in df_date.columns else 0.0
        npa_pct = round(total_npa / total_adv * 100, 2) if total_adv > 0 else 0.0

        kpis = {
            "Total Advances": _clean_value(total_adv),
            "Total Deposits": _clean_value(
                float(df_date["TOTAL DEPOSITS"].sum())
            ) if "TOTAL DEPOSITS" in df_date.columns else 0.0,
            "NPA Amount": _clean_value(total_npa),
            "NPA %": _clean_value(npa_pct),
            "CD Ratio": _clean_value(
                round(float(df_date["CD RATIO"].mean()), 2)
            ) if "CD RATIO" in df_date.columns else 0.0,
        }

        return {
            "kpis": kpis,
            "selected_date": str(selected_date),
            "row_count": len(df_date),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/trend")
def get_mis_trend(
    sols: Optional[str] = Query(None, description="Comma-separated SOL codes"),
):
    """
    FY growth trend — last 12 date points with summed ADV and TOTAL DEPOSITS.
    Returns: {trend: [{date, advances, deposits}]}
    """
    try:
        from src.infrastructure.persistence.mis_repository import MISRepository

        sol_list = (
            [int(s.strip()) for s in sols.split(",") if s.strip()]
            if sols
            else None
        )

        repo = MISRepository()
        df = repo.load_frame()
        if df.empty:
            return {"trend": []}

        df.columns = [c.upper().replace("_", " ") for c in df.columns]
        df["DATE"] = pd.to_datetime(df["DATE"])

        if "TOTAL DEPOSITS" not in df.columns:
            deps_cols = [c for c in ["SB", "CD", "TD"] if c in df.columns]
            df["TOTAL DEPOSITS"] = df[deps_cols].fillna(0).sum(axis=1) if deps_cols else 0.0
        if "ADV" not in df.columns:
            df["ADV"] = 0.0

        # Exclude RO aggregate SOL
        if "SOL" in df.columns:
            df = df[df["SOL"] != 3933]

        if sol_list and "SOL" in df.columns:
            df = df[df["SOL"].isin(sol_list)]

        grouped = (
            df.groupby("DATE", as_index=False)[["ADV", "TOTAL DEPOSITS"]].sum()
        )
        grouped = grouped.sort_values("DATE").tail(12)

        trend = [
            {
                "date": row["DATE"].strftime("%Y-%m-%d"),
                "advances": _clean_value(float(row["ADV"])),
                "deposits": _clean_value(float(row["TOTAL DEPOSITS"])),
            }
            for _, row in grouped.iterrows()
        ]

        return {"trend": trend}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/milestones")
def get_mis_milestones(
    date: Optional[str] = Query(None, description="Reporting date YYYY-MM-DD (defaults to latest)"),
):
    """
    Milestone list and breakthrough events for the given reporting date.
    Returns: {milestones: list, breakthroughs: list}
    """
    try:
        from src.application.services.milestone_service import MilestoneService
        from src.infrastructure.persistence.database import get_db_session
        from src.infrastructure.persistence.mis_repository import MISRepository

        repo = MISRepository()
        available_dates = repo.get_available_dates()
        if not available_dates:
            return {"milestones": [], "breakthroughs": []}

        if date:
            try:
                selected_date = datetime.date.fromisoformat(date)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid date: '{date}'. Use YYYY-MM-DD.")
        else:
            selected_date = available_dates[-1]

        with get_db_session() as session:
            ms = MilestoneService(session)
            milestones = ms.get_all_at_milestones() or []
            breakthroughs = ms.get_milestone_achievements(target_date=selected_date) or []

        return {"milestones": milestones, "breakthroughs": breakthroughs}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/performers")
def get_mis_performers(
    date: Optional[str] = Query(None, description="Reporting date YYYY-MM-DD (defaults to latest)"),
    metric: str = Query("ADV", description="Metric column, e.g. ADV, TOTAL DEPOSITS, NPA"),
    basis: str = Query("actual", description="Basis: actual (future: growth)"),
):
    """
    Top 5 and bottom 5 branch performers for a given metric on a given date.
    Returns: {top: [{sol, branch_name, value}], bottom: [...], metric, date}
    """
    try:
        from src.infrastructure.persistence.master_repository import MasterRepository

        df_all, df_date, selected_date = _load_enriched_frame(date)
        if selected_date is None or df_date is None or df_date.empty:
            return {
                "top": [],
                "bottom": [],
                "metric": metric.upper(),
                "date": str(selected_date) if selected_date else None,
            }

        metric_upper = metric.upper()
        if metric_upper not in df_date.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Metric '{metric}' not found. Available columns: {list(df_date.columns)}",
            )

        # Map SOL → branch name from master data
        master_repo = MasterRepository()
        units = {str(u.code): u.name_en for u in master_repo.get_by_category("UNIT")}

        # Group by SOL, sum the metric
        grouped = df_date.groupby("SOL", as_index=False)[metric_upper].sum()
        grouped = grouped.dropna(subset=[metric_upper])
        grouped = grouped.sort_values(metric_upper, ascending=False)

        def _make_row(r):
            sol_str = str(int(r["SOL"]))
            return {
                "sol": sol_str,
                "branch_name": units.get(sol_str, f"Branch {sol_str}"),
                "value": _clean_value(float(r[metric_upper])),
            }

        top_5 = [_make_row(r) for _, r in grouped.head(5).iterrows()]
        bottom_5 = [_make_row(r) for _, r in grouped.tail(5).iterrows()]

        return {
            "top": top_5,
            "bottom": bottom_5,
            "metric": metric_upper,
            "date": str(selected_date),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
