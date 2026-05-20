from __future__ import annotations

import datetime
import shutil

import numpy as np
import pandas as pd
import streamlit as st

from src.core.config.config_loader import get_app_settings
from src.core.paths import project_path
from src.core.utils.financial_year import get_fy_start, get_quarter_start, get_next_month_end, get_fy_end
from src.domain.schemas.mis import MISFilter, MISSnapshot
from src.infrastructure.persistence.excel_repo import ExcelRepository
from src.infrastructure.persistence.mis_repository import MISRepository
from src.infrastructure.persistence.budget_repository import BudgetRepository
from src.application.services.milestone_service import MilestoneService
from src.infrastructure.persistence.database import get_db_session


class MISAnalyticsService:
    def __init__(self) -> None:
        self.settings = get_app_settings()
        self.mis_dir = project_path("data", "mis")
        self.archive_dir = self.mis_dir / "archive"
        self.excel_repo = ExcelRepository()
        self.repository = MISRepository()
        self.budget_repo = BudgetRepository()
        from src.core.registry.parameter_service import ParameterRegistry
        self.registry = ParameterRegistry()

    def sync_database(self, progress_callback: callable | None = None) -> list[dict]:
        """Explicitly triggers synchronization of database with any new MIS Excel files."""
        return self._ingest_new_files(progress_callback)

    def _ingest_new_files(self, progress_callback: callable | None = None) -> list[dict]:
        self.mis_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        summaries = []
        
        files = list(self.mis_dir.glob("*.xlsx"))
        total_files = len(files)
        
        for i, file_path in enumerate(files):
            if progress_callback:
                progress_callback((i + 1) / total_files, f"Processing {file_path.name} ({i+1}/{total_files})")
                
            # Process everything in mis_dir; files are moved to archive/ after success
            frame = self.excel_repo.read(file_path)
            if frame.empty:
                continue
                
            if "DATE" in frame.columns:
                frame["DATE"] = pd.to_datetime(
                    frame["DATE"].astype(str).str.split(".").str[0],
                    format="%Y%m%d",
                    errors="coerce",
                )
            
            dates_in_file = frame["DATE"].dropna().dt.date.unique().tolist()
            date_str = ", ".join([d.strftime("%d-%b-%Y") for d in dates_in_file])
            
            self.repository.save_records(frame.to_dict("records"))
            self.repository.mark_file_ingested(file_path.name)
            
            summaries.append({
                "filename": file_path.name,
                "dates": date_str,
                "count": len(frame)
            })
            
            shutil.move(str(file_path), str(self.archive_dir / file_path.name))
        
        # Clear cache after ingestion
        self.load_frame.clear()
        return summaries

    def delete_mis_file(self, filename: str) -> bool:
        """Permanently deletes an archived MIS file and its database records."""
        file_path = self.archive_dir / filename
        
        # 1. Identify dates in the file to clean up DB records
        dates_to_clean = []
        if file_path.exists():
            try:
                frame = self.excel_repo.read(file_path)
                if not frame.empty and "DATE" in frame.columns:
                    # Normalize dates
                    frame["DATE"] = pd.to_datetime(
                        frame["DATE"].astype(str).str.split(".").str[0],
                        format="%Y%m%d",
                        errors="coerce",
                    )
                    dates_to_clean = frame["DATE"].dropna().dt.date.unique().tolist()
            except Exception as e:
                st.error(f"Error reading file before deletion: {e}")

        # 2. Delete DB records for those dates
        if dates_to_clean:
            with get_db_session() as session:
                from src.infrastructure.persistence.sqlite_models import MISRecordModel, MilestoneAchievementModel
                # Remove raw data
                session.query(MISRecordModel).filter(MISRecordModel.date.in_(dates_to_clean)).delete(synchronize_session=False)
                # Remove associated breakthroughs to prevent ghost milestones from deleted dates
                session.query(MilestoneAchievementModel).filter(MilestoneAchievementModel.date.in_(dates_to_clean)).delete(synchronize_session=False)
                session.commit()

        # 3. Delete physical file
        if file_path.exists():
            file_path.unlink()
        
        # 4. Remove from DB tracking (IngestedFileModel)
        success = self.repository.delete_ingested_file(filename)
        
        # Clear cache to reflect changes
        self.load_frame.clear()
        return success

    def delete_records_by_date(self, target_date: datetime.date) -> tuple[int, int]:
        with get_db_session() as session:
            from src.infrastructure.persistence.sqlite_models import MISRecordModel, MilestoneAchievementModel
            r_cnt = session.query(MISRecordModel).filter(MISRecordModel.date == target_date).delete(synchronize_session=False)
            m_cnt = session.query(MilestoneAchievementModel).filter(MilestoneAchievementModel.date == target_date).delete(synchronize_session=False)
            session.commit()
            
        self.load_frame.clear()
        return r_cnt, m_cnt

    def save_milestone_achievements(self, achievements: list[dict]) -> int:
        with get_db_session() as session:
            ms = MilestoneService(session)
            saved_count = ms.save_achievements(achievements)
            return saved_count

    def get_available_dates(self) -> list:
        return self.repository.get_available_dates()

    def get_available_sols(self) -> list:
        return self.repository.get_available_sols()

    @st.cache_data(show_spinner=True)
    def load_frame(_self, start_date=None, end_date=None) -> pd.DataFrame:
        """Cached data loading and enrichment."""
        frame = _self.repository.load_frame(start_date, end_date)
        if frame.empty:
            return frame
        frame.columns = [column.upper().replace("_", " ") for column in frame.columns]
        frame["DATE"] = pd.to_datetime(frame["DATE"])
        frame = _self._enrich_metrics(frame)
        
        # Exclude Regional Office SOL (3933) at the cache layer as it contains 
        # aggregate figures and would cause double-counting.
        # Filtering it here prevents Streamlit from creating a deep copy of the DataFrame
        # for every single user session.
        if "SOL" in frame.columns:
            frame = frame[frame["SOL"] != 3933]
            
        return frame

    def get_data(self, force_ingest: bool = False, start_date=None, end_date=None) -> pd.DataFrame:
        """Main entry point for UI, handles ingestion before loading."""
        if force_ingest or st.session_state.get("mis_needs_ingest", True):
            mis_dir = getattr(self, "mis_dir", None)
            if mis_dir is not None and any(mis_dir.glob("*.xlsx")):
                self._ingest_new_files()
            st.session_state["mis_needs_ingest"] = False
            
        return self.load_frame(start_date, end_date)

    def _enrich_metrics(self, frame: pd.DataFrame) -> pd.DataFrame:
        def safe_sum(df, columns):
            existing = [column for column in columns if column in df.columns]
            return df[existing].fillna(0).sum(axis=1) if existing else 0

        def enrich_category(df, parent_id):
            p_config = self.registry.get_by_id(parent_id)
            if not p_config: return df
            col = p_config["mis_col"]
            if col not in df.columns or df[col].fillna(0).sum() == 0:
                subsets = self.registry.get_subset_map(parent_id)
                df[col] = safe_sum(df, subsets)
            return df

        for cat_id in ["core_retail", "casa", "core_agri", "msme", "gold"]:
            frame = enrich_category(frame, cat_id)
        
        # Ensure ADV exists to prevent downstream errors
        if "ADV" not in frame.columns:
            frame["ADV"] = 0.0

        frame["TOTAL DEPOSITS"] = safe_sum(frame, ["SB", "CD", "TD"])
        
        frame["CD RATIO"] = np.where(frame["TOTAL DEPOSITS"] > 0, frame["ADV"] / frame["TOTAL DEPOSITS"] * 100, 0).round(2)
        frame["TOTAL CASH"] = safe_sum(frame, ["CASH ON HAND", "ATM CASH", "BC CASH", "BNA CASH"])
        crl = frame["CRL"].fillna(0) if "CRL" in frame.columns else 0
        frame["CASH VS CRL"] = frame["TOTAL CASH"] - crl
        frame["TOTAL RECOVERY"] = safe_sum(frame, ["REC Q1", "REC Q2", "REC Q3", "REC Q4"])
        npa = frame["NPA"].fillna(0) if "NPA" in frame.columns else 0
        frame["NPA %"] = np.where(frame["ADV"] > 0, npa / frame["ADV"] * 100, 0).round(2)
        return frame

    @st.cache_resource(show_spinner=False, ttl=3600)
    def build_snapshot(_self, filters_dict: dict | MISFilter | None) -> MISSnapshot | None:
        """Cached snapshot builder accepting either a MISFilter model or a cache-friendly dict."""
        if isinstance(filters_dict, MISFilter):
            filters_dict = filters_dict.model_dump()

        selected_date = filters_dict.get("selected_date") if filters_dict else None
        if not selected_date:
            avail = _self.get_available_dates()
            selected_date = avail[-1] if avail else datetime.date.today()
            
        fy_start = get_fy_start(selected_date)
        start_date = fy_start - datetime.timedelta(days=366)

        frame = _self.get_data(start_date=start_date, end_date=selected_date)
        if frame.empty:
            return None
        frame = frame.copy()
        frame.columns = [column.upper().replace("_", " ") for column in frame.columns]
        if "ADV" not in frame.columns and "TOTAL ADVANCES" in frame.columns:
            frame["ADV"] = frame["TOTAL ADVANCES"]
        if "TOTAL DEPOSITS" not in frame.columns and "TOTAL DEPOSIT" in frame.columns:
            frame["TOTAL DEPOSITS"] = frame["TOTAL DEPOSIT"]
        if "DATE" in frame.columns:
            frame["DATE"] = pd.to_datetime(frame["DATE"])
        
        dates = sorted(frame["DATE"].dropna().dt.date.unique())
        sols = filters_dict.get("sols") if filters_dict else None
        
        selected = frame[frame["DATE"].dt.date == selected_date].copy()
        history = frame.copy()
        
        if sols:
            selected = selected[selected["SOL"].isin(sols)]
            history = history[history["SOL"].isin(sols)]
        # No special handling for aggregate_sol needed here, as get_data() already filters out 
        # the RO SOL to prevent double-counting. We always work with the sum of branches.
        pass

        total_adv = float(selected["ADV"].sum()) if "ADV" in selected.columns else 0.0
        total_npa = float(selected["NPA"].sum()) if "NPA" in selected.columns else 0.0
        npa_pct = (total_npa / total_adv * 100) if total_adv > 0 else 0.0
        
        kpis = {
            "Total Advances": total_adv,
            "Total Deposits": float(selected["TOTAL DEPOSITS"].sum()) if "TOTAL DEPOSITS" in selected.columns else 0.0,
            "NPA Amount": total_npa,
            "NPA %": npa_pct,
            "CD Ratio": float(selected["CD RATIO"].mean()) if "CD RATIO" in selected.columns else 0.0,
        }
        
        milestones = None
        milestone_breakthroughs = None
        with get_db_session() as session:
            ms = MilestoneService(session)
            milestones = ms.get_all_at_milestones()
            # Calculate breakthroughs for the month of the selected reporting date
            milestone_breakthroughs = ms.get_milestone_achievements(target_date=selected_date)

        avail_sols = sorted(frame["SOL"].dropna().astype(int).unique().tolist()) if "SOL" in frame.columns else []
        return MISSnapshot(
            selected_date=selected_date,
            available_dates=dates,
            available_sols=avail_sols,
            kpis=kpis,
            rows=selected.to_dict("records"),
            history_rows=history.to_dict("records"),
            milestones=milestones,
            milestone_breakthroughs=milestone_breakthroughs
        )

    @st.cache_data(show_spinner=False)
    def get_performance_metrics(_self, selected_date: datetime.date, metric_name: str = "ADV", sols: list[int] | None = None) -> dict:
        fy_start = get_fy_start(selected_date)
        start_date = fy_start - datetime.timedelta(days=366)
        frame = _self.get_data(start_date=start_date, end_date=selected_date)
        if frame.empty:
            return {}

        metric_name = metric_name.upper()
        filtered_history = frame.copy()
        if sols:
            filtered_history = filtered_history[filtered_history["SOL"].isin(sols)]
        # Special regional logic removed; get_data() already handles RO SOL filtering.
        pass

        fy_start = get_fy_start(selected_date)
        prev_fy_end = fy_start - datetime.timedelta(days=1)
        current_data = filtered_history[filtered_history["DATE"].dt.date == selected_date]
        current_val = current_data[metric_name].sum() if not current_data.empty and metric_name in current_data.columns else 0.0

        # FY Growth Baseline should be the closest date <= prev_fy_end (typically March 31st)
        prev_dates = filtered_history[filtered_history["DATE"].dt.date <= prev_fy_end]["DATE"].unique()
        if len(prev_dates) > 0:
            baseline_date = sorted(prev_dates, reverse=True)[0]
            fy_start_data = filtered_history[filtered_history["DATE"] == baseline_date]
        else:
            # If no previous FY data exists, fallback to the earliest available date overall
            earliest_dates = filtered_history["DATE"].unique()
            if len(earliest_dates) > 0:
                earliest_date = sorted(earliest_dates)[0]
                fy_start_data = filtered_history[filtered_history["DATE"] == earliest_date]
            else:
                fy_start_data = pd.DataFrame()
        
        fy_start_val = fy_start_data[metric_name].sum() if not fy_start_data.empty and metric_name in fy_start_data.columns else 0.0

        fy_growth = current_val - fy_start_val
        fy_growth_pct = (fy_growth / fy_start_val * 100) if fy_start_val > 0 else 0.0

        curr_month_str = selected_date.strftime("%Y-%m")
        next_month_date = get_next_month_end(selected_date)
        next_month_str = next_month_date.strftime("%Y-%m")

        target_curr_month = _self.budget_repo.get_target(metric_name, curr_month_str, sols=sols)
        target_next_month = _self.budget_repo.get_target(metric_name, next_month_str, sols=sols)
        
        fy_end = get_fy_end(selected_date)
        fy_end_str = fy_end.strftime("%Y-%m")
        target_fy = _self.budget_repo.get_target(metric_name, fy_end_str, sols=sols)

        return {
            "current_actual": current_val,
            "fy_start_actual": fy_start_val,
            "fy_growth": fy_growth,
            "fy_growth_pct": fy_growth_pct,
            "gap_current_month": target_curr_month - current_val,
            "gap_next_month": target_next_month - current_val,
            "gap_fy": target_fy - current_val,
            "targets": {
                "month": target_curr_month,
                "next_month": target_next_month,
                "fy": target_fy
            }
        }
