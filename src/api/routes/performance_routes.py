from __future__ import annotations

import datetime
import math
from typing import Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from src.infrastructure.persistence.master_repository import MasterRepository

router = APIRouter()


def _clean_value(v):
    """Return None for NaN / Inf floats."""
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


@router.get("/branches")
def get_branch_performance(
    date: Optional[str] = Query(
        None, description="Reporting date YYYY-MM-DD (defaults to latest available)"
    ),
    metric: str = Query("ADV", description="Metric column name, e.g. ADV, TOTAL DEPOSITS, NPA"),
):
    """
    Branch-wise performance for a given metric on a given date,
    sorted descending by metric value.
    Returns: {branches: [{sol, name, value, date}], metric, date}
    """
    try:
        from src.infrastructure.persistence.mis_repository import MISRepository

        repo = MISRepository()
        available_dates = repo.get_available_dates()
        if not available_dates:
            return {"branches": [], "metric": metric.upper(), "date": None}

        # Resolve reporting date
        if date:
            try:
                selected_date = datetime.date.fromisoformat(date)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid date format: '{date}'. Use YYYY-MM-DD.",
                )
        else:
            selected_date = available_dates[-1]

        # Load raw frame
        df = repo.load_frame()
        if df.empty:
            return {"branches": [], "metric": metric.upper(), "date": str(selected_date)}

        df.columns = [c.upper().replace("_", " ") for c in df.columns]
        df["DATE"] = pd.to_datetime(df["DATE"])

        # Derived deposits column
        if "TOTAL DEPOSITS" not in df.columns:
            deps_cols = [c for c in ["SB", "CD", "TD"] if c in df.columns]
            df["TOTAL DEPOSITS"] = (
                df[deps_cols].fillna(0).sum(axis=1) if deps_cols else 0.0
            )
        if "ADV" not in df.columns:
            df["ADV"] = 0.0

        # Exclude RO aggregate SOL
        if "SOL" in df.columns:
            df = df[df["SOL"] != 3933]

        # Filter to selected date
        df_date = df[df["DATE"].dt.date == selected_date].copy()
        if df_date.empty:
            return {"branches": [], "metric": metric.upper(), "date": str(selected_date)}

        metric_upper = metric.upper()
        if metric_upper not in df_date.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Metric '{metric}' not found. Available columns: {sorted(df_date.columns.tolist())}",
            )

        # Map SOL → branch name
        master_repo = MasterRepository()
        units = {str(u.code): u.name_en for u in master_repo.get_by_category("UNIT")}

        # Group by SOL, sum metric, sort descending
        grouped = (
            df_date.groupby("SOL", as_index=False)[metric_upper]
            .sum()
            .dropna(subset=[metric_upper])
            .sort_values(metric_upper, ascending=False)
        )

        branches = []
        for _, row in grouped.iterrows():
            sol_str = str(int(row["SOL"]))
            branches.append(
                {
                    "sol": sol_str,
                    "name": units.get(sol_str, f"Branch {sol_str}"),
                    "value": _clean_value(float(row[metric_upper])),
                    "date": str(selected_date),
                }
            )

        return {"branches": branches, "metric": metric_upper, "date": str(selected_date)}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
