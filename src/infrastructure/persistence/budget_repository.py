import os
import json
import logging
import pandas as pd
from typing import List
import datetime
import calendar
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from src.core.paths import project_path
from src.infrastructure.persistence.json_repo import JsonRepository
from src.infrastructure.persistence.sqlite_models import Base, BudgetModel

logger = logging.getLogger(__name__)

class BudgetRepository:
    def __init__(self) -> None:
        self.excel_path = project_path("samples", "budgets2.xlsx")
        self.db_path = project_path("data", "mis_store.db")
        
        from src.core.registry.parameter_service import ParameterRegistry
        self.registry = ParameterRegistry()
        self.param_map = self.registry.get_mis_to_budget_map()

        self.engine = create_engine(f"sqlite:///{self.db_path.as_posix()}")
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        
        self.json_repo = JsonRepository(
            project_path("data", "budgets.json"),
            {"defaults": {"TOTAL ADVANCES": 500000.0}}
        )
        
        # Automatically sync if file changed
        self.sync_if_needed()

    def sync_if_needed(self):
        """Checks if CSV was modified since last ingestion and re-syncs if needed."""
        csv_path = project_path("files", "Budget3.csv")
        if not csv_path.exists():
            return

        file_mtime = os.path.getmtime(csv_path)
        file_size = os.path.getsize(csv_path)
        
        sync_meta_path = project_path("data", "budget_sync.json")
        if os.path.exists(sync_meta_path):
            try:
                with open(sync_meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    if meta.get("mtime") == file_mtime and meta.get("size") == file_size:
                        return # No changes
            except (OSError, json.JSONDecodeError) as exc:
                logger.warning("Ignoring unreadable budget sync state %s: %s", sync_meta_path, exc)

        self._ingest_csv(csv_path)
        
        with open(sync_meta_path, "w", encoding="utf-8") as f:
            json.dump({"mtime": file_mtime, "size": file_size}, f)

    def _ingest_csv(self, csv_path) -> None:
        """Reads CSV and saves to SQLite."""
        try:
            df = pd.read_csv(csv_path)
            # Cleanup column names (remove leading/trailing spaces)
            df.columns = [c.strip() for c in df.columns]
            
            # Period is Mar-26, Apr-26 etc. Force to end of month explicitly
            df["DATE"] = pd.to_datetime(df["Period"], format="%b-%y")
            df["DATE"] = df["DATE"].apply(lambda x: x.replace(day=pd.Period(x, freq='M').days_in_month))
            
            session = self.session_factory()
            try:
                # Identify dates to update/replace
                incoming_dates = df["DATE"].dt.date.unique()
                
                # Delete only the overlapping records to maintain history
                session.query(BudgetModel).filter(BudgetModel.date.in_(incoming_dates)).delete(synchronize_session=False)
                
                def safe_float(val):
                    try:
                        v = str(val).replace(",", "").strip()
                        if v in ["-", "", "None", "nan"]: return 0.0
                        return float(v)
                    except (TypeError, ValueError):
                        return 0.0

                objects = []
                for _, row in df.iterrows():
                    objects.append(BudgetModel(
                        sol=int(row["SOL"]),
                        parameter=str(row["PARAMETER"]).strip(),
                        date=row["DATE"].date(),
                        target=safe_float(row["Value"])
                    ))
                
                session.bulk_save_objects(objects)
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
        except Exception as e:
            logger.exception("Budget sync failed for %s: %s", csv_path, e)

    def get_monthly_targets(self, sols: List[int], fy_start: datetime.date) -> pd.DataFrame:
        """Returns a pivot table of monthly targets for the FY, including the baseline."""
        fy_end = fy_start.replace(year=fy_start.year + 1)
        
        # Explicitly use the end of the previous FY (March 31st)
        prev_fy_end = fy_start - datetime.timedelta(days=1)
        
        session = self.session_factory()
        try:
            # Exclude Regional Office SOL (3933) to prevent double counting
            region_code = self.registry.get_org_info().get("region_code")
            try:
                ro_sol = int(region_code) if region_code else 3933
            except ValueError:
                ro_sol = 3933

            sols_filtered = [s for s in sols if s != ro_sol]

            query = session.query(BudgetModel).filter(
                BudgetModel.sol.in_(sols_filtered),
                BudgetModel.date >= prev_fy_end,
                BudgetModel.date < fy_end
            )
            df = pd.read_sql(query.statement, self.engine)
            if df.empty:
                return pd.DataFrame()
            
            # Pivot to get Parameter vs Date
            df["Month"] = pd.to_datetime(df["date"]).dt.strftime("%b-%y")
            # Keep months in chronological order
            month_order = []
            curr = prev_fy_end
            while curr < fy_end:
                month_order.append(curr.strftime("%b-%y"))
                # Safely advance exactly to the last day of the next month
                next_month = 1 if curr.month == 12 else curr.month + 1
                next_year = curr.year + 1 if curr.month == 12 else curr.year
                _, last_day = calendar.monthrange(next_year, next_month)
                curr = datetime.date(next_year, next_month, last_day)

            pivot = df.pivot_table(
                index="parameter", 
                columns="Month", 
                values="target", 
                aggfunc="sum"
            )
            # Reorder columns
            existing_cols = [m for m in month_order if m in pivot.columns]
            return pivot[existing_cols]
        finally:
            session.close()

    def get_target(self, metric: str, year_month: str | None = None, sols: List[int] | None = None) -> float:
        """Retrieves aggregated budget target from SQLite."""
        excel_param = self.param_map.get(metric.upper(), self.param_map.get(metric, metric))
        
        session = self.session_factory()
        try:
            # Exclude Regional Office SOL (3933) to prevent double counting
            region_code = self.registry.get_org_info().get("region_code")
            try:
                ro_sol = int(region_code) if region_code else 3933
            except ValueError:
                ro_sol = 3933

            query = session.query(func.sum(BudgetModel.target)).filter(BudgetModel.parameter == excel_param)
            
            if sols:
                sols_filtered = [s for s in sols if s != ro_sol]
                query = query.filter(BudgetModel.sol.in_(sols_filtered))
            else:
                query = query.filter(BudgetModel.sol != ro_sol)
            
            if year_month:
                target_dt = pd.to_datetime(year_month).date()
                # Match year and month
                first_day = target_dt.replace(day=1)
                if target_dt.month == 12:
                    last_day = target_dt.replace(year=target_dt.year + 1, month=1, day=1)
                else:
                    last_day = target_dt.replace(month=target_dt.month + 1, day=1)
                
                query = query.filter(BudgetModel.date >= first_day, BudgetModel.date < last_day)
            
            result = query.scalar()
            if result is not None:
                return float(result)
        except Exception as e:
            logger.exception("Budget query failed for %s: %s", metric, e)
        finally:
            session.close()

        # Fallback to JSON defaults
        data = self.json_repo.read()
        return float(data.get("defaults", {}).get(metric, 0.0))

    def get_sync_status(self) -> dict:
        """Returns metadata about stored budgets."""
        sync_meta_path = project_path("data", "budget_sync.json")
        last_sync = "Never"
        if os.path.exists(sync_meta_path):
            try:
                with open(sync_meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    mtime = meta.get("mtime", 0)
                    last_sync = datetime.datetime.fromtimestamp(mtime).strftime("%d-%m-%Y %H:%M")
            except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
                logger.warning("Ignoring unreadable budget sync status %s: %s", sync_meta_path, exc)
            
        session = self.session_factory()
        fy_ranges = []
        try:
            # Get distinct years from DB
            dates = session.query(BudgetModel.date).distinct().all()
            years = sorted(list(set([d[0].year for d in dates])))
            # Convert years to FY ranges (assuming April start)
            # If we have 2026-04, that's FY 2026-27
            for y in years:
                fy_ranges.append(f"{y}-{str(y+1)[2:]}")
        finally:
            session.close()
            
        return {
            "last_sync": last_sync,
            "fy_ranges": sorted(list(set(fy_ranges)))
        }
