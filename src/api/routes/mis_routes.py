from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import pandas as pd
import math

from src.application.use_cases.mis.service import MISAnalyticsService

router = APIRouter()
# We instantiate a single service instance for the router
mis_service = MISAnalyticsService()

@router.get("/data")
def get_mis_data(
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
    force_ingest: bool = Query(False, description="Force re-ingestion of Excel files before loading")
):
    """
    Fetch the complete MIS dataset.
    """
    try:
        df = mis_service.get_data(force_ingest=force_ingest, start_date=start_date, end_date=end_date)
        if df.empty:
            return {"data": [], "message": "No data found for the given parameters."}
        
        # Replace NaN and Infinity with None so it's JSON serializable
        df = df.replace([pd.NA, math.nan, float('inf'), float('-inf')], None)
        
        # Convert datetime columns to strings
        for col in df.select_dtypes(include=['datetime64[ns]']).columns:
            df[col] = df[col].dt.strftime('%Y-%m-%d')
            
        return {"data": df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/available-dates")
def get_available_dates():
    """
    Get a list of dates for which MIS data is available.
    """
    try:
        dates = mis_service.get_available_dates()
        return {"dates": [d.strftime('%Y-%m-%d') for d in dates]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
