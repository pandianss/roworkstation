from __future__ import annotations

import datetime
import io
import pandas as pd
from sqlalchemy import func
from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.persistence.sqlite_models import AccountOpeningModel, AccountClosureModel
from src.infrastructure.persistence.master_repository import MasterRepository

class AccountPerformanceService:
    def __init__(self) -> None:
        from src.infrastructure.persistence.database import engine
        from src.infrastructure.persistence.sqlite_models import Base
        Base.metadata.create_all(engine)
        self.master_repo = MasterRepository()

    def calculate_working_days(
        self,
        start_date: datetime.date,
        end_date: datetime.date,
        exclude_2nd_4th_sat: bool = True
    ) -> int:
        """
        Calculates the number of banking working days between two dates inclusive.
        Excludes Sundays, and optionally 2nd and 4th Saturdays of any month.
        Also excludes public holidays configured in the calendar.
        """
        if start_date > end_date:
            return 0

        # Fetch active public holidays in range from DB
        from src.infrastructure.persistence.sqlite_models import MasterRecordModel
        with get_db_session() as session:
            holiday_records = session.query(MasterRecordModel.code).filter(
                MasterRecordModel.category == "HOLIDAY",
                MasterRecordModel.is_active == True,
                MasterRecordModel.code >= start_date.strftime("%Y-%m-%d"),
                MasterRecordModel.code <= end_date.strftime("%Y-%m-%d")
            ).all()
            public_holidays = {r[0] for r in holiday_records}

        working_days = 0
        current_date = start_date
        while current_date <= end_date:
            weekday = current_date.weekday() # Monday=0, Sunday=6, Saturday=5
            date_str = current_date.strftime("%Y-%m-%d")
            
            if date_str in public_holidays:
                is_holiday = True
            elif weekday == 6:
                # Sunday is always a holiday
                is_holiday = True
            elif weekday == 5 and exclude_2nd_4th_sat:
                # Saturday - check if 2nd or 4th Saturday
                week_index = (current_date.day - 1) // 7
                if week_index in (1, 3):
                    is_holiday = True
                else:
                    is_holiday = False
            else:
                is_holiday = False

            if not is_holiday:
                working_days += 1

            current_date += datetime.timedelta(days=1)

        return working_days

    def get_public_holidays(self) -> list[dict]:
        """
        Retrieves all public holidays from the masters database table.
        """
        from src.infrastructure.persistence.sqlite_models import MasterRecordModel
        with get_db_session() as session:
            records = session.query(MasterRecordModel).filter(
                MasterRecordModel.category == "HOLIDAY",
                MasterRecordModel.is_active == True
            ).order_by(MasterRecordModel.code.asc()).all()
            
            return [
                {
                    "date": r.code,
                    "name": r.name_en
                }
                for r in records
            ]

    def add_public_holiday(self, date_val: datetime.date, name: str) -> None:
        """
        Adds or updates a public holiday in the masters database table.
        """
        from src.infrastructure.persistence.sqlite_models import MasterRecordModel
        date_str = date_val.strftime("%Y-%m-%d")
        with get_db_session() as session:
            existing = session.query(MasterRecordModel).filter(
                MasterRecordModel.category == "HOLIDAY",
                MasterRecordModel.code == date_str
            ).first()
            
            if existing:
                existing.name_en = name
                existing.is_active = True
            else:
                new_holiday = MasterRecordModel(
                    category="HOLIDAY",
                    code=date_str,
                    name_en=name,
                    is_active=True
                )
                session.add(new_holiday)
            session.commit()

    def delete_public_holiday(self, date_str: str) -> None:
        """
        Deletes a public holiday from the masters database table.
        """
        from src.infrastructure.persistence.sqlite_models import MasterRecordModel
        with get_db_session() as session:
            session.query(MasterRecordModel).filter(
                MasterRecordModel.category == "HOLIDAY",
                MasterRecordModel.code == date_str
            ).delete()
            session.commit()

    def import_openings_csv(self, file_bytes: bytes) -> dict:
        """
        Parses Open.csv and updates the database, returning ingestion summary stats.
        """
        df = pd.read_csv(io.BytesIO(file_bytes))
        if df.empty:
            return {"count": 0, "dates": []}

        # Normalize column headers (strip spaces, lowercase, replace spaces with underscores)
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

        # Column mapping
        col_mapping = {
            "sol_id": ["sol_id", "sol", "branch"],
            "schm_type": ["schm_type", "sch_type", "type"],
            "schm_code": ["schm_code", "sch_code", "code"],
            "acct_opn_date": ["acct_opn_date", "opn_date", "date", "acct_opn_dt"],
            "clr_bal_amt": ["clr_bal_amt", "clr_bal", "balance", "bal"],
            "average_balance": ["average_balance", "average_balance_amt", "avg_bal", "avg_balance"]
        }

        resolved_cols = {}
        for target, aliases in col_mapping.items():
            for alias in aliases:
                if alias in df.columns:
                    resolved_cols[target] = alias
                    break

        if "sol_id" not in resolved_cols or "acct_opn_date" not in resolved_cols or "schm_type" not in resolved_cols:
            raise ValueError("CSV missing required columns. Ensure SOL_ID, ACCT_OPN_DATE, and SCHM_TYPE are present.")

        # Clean and extract records
        records_to_insert = []
        unique_dates = set()

        for _, row in df.iterrows():
            try:
                sol = int(float(row[resolved_cols["sol_id"]]))
            except (ValueError, TypeError):
                continue

            schm_type = str(row[resolved_cols["schm_type"]]).strip().upper()
            schm_code = str(row.get(resolved_cols.get("schm_code"), "")).strip().upper()
            
            raw_date = str(row[resolved_cols["acct_opn_date"]]).strip()
            try:
                opn_date = datetime.datetime.strptime(raw_date, "%d.%m.%Y").date()
            except ValueError:
                try:
                    opn_date = pd.to_datetime(raw_date, errors="raise").date()
                except Exception:
                    continue

            try:
                clr_bal = float(row.get(resolved_cols.get("clr_bal_amt"), 0.0))
            except (ValueError, TypeError):
                clr_bal = 0.0

            try:
                avg_bal = float(row.get(resolved_cols.get("average_balance"), 0.0))
            except (ValueError, TypeError):
                avg_bal = 0.0

            unique_dates.add(opn_date)
            records_to_insert.append({
                "sol_id": sol,
                "schm_type": schm_type,
                "schm_code": schm_code,
                "acct_opn_date": opn_date,
                "clr_bal_amt": clr_bal,
                "average_balance": avg_bal
            })

        if not records_to_insert:
            return {"count": 0, "dates": []}

        # Clear existing records for the same dates to support idempotent re-upload
        dates_list = sorted(list(unique_dates))
        with get_db_session() as session:
            session.query(AccountOpeningModel).filter(
                AccountOpeningModel.acct_opn_date.in_(dates_list)
            ).delete(synchronize_session=False)

            objects = [AccountOpeningModel(**rec) for rec in records_to_insert]
            session.bulk_save_objects(objects)
            session.commit()

        return {
            "count": len(records_to_insert),
            "dates": [d.strftime("%Y-%m-%d") for d in dates_list]
        }

    def import_closures_csv(self, file_bytes: bytes) -> dict:
        """
        Parses Closure (1).csv and updates the database, returning ingestion summary stats.
        """
        df = pd.read_csv(io.BytesIO(file_bytes))
        if df.empty:
            return {"count": 0, "dates": []}

        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

        col_mapping = {
            "sol_id": ["sol_id", "sol", "branch"],
            "acct_cls_date": ["acct_cls_date", "cls_date", "date", "acct_cls_dt"],
            "schm_type": ["schm_type", "sch_type", "type"]
        }

        resolved_cols = {}
        for target, aliases in col_mapping.items():
            for alias in aliases:
                if alias in df.columns:
                    resolved_cols[target] = alias
                    break

        if "sol_id" not in resolved_cols or "acct_cls_date" not in resolved_cols or "schm_type" not in resolved_cols:
            raise ValueError("CSV missing required columns. Ensure SOL_ID, ACCT_CLS_DATE, and SCHM_TYPE are present.")

        records_to_insert = []
        unique_dates = set()

        for _, row in df.iterrows():
            try:
                sol = int(float(row[resolved_cols["sol_id"]]))
            except (ValueError, TypeError):
                continue

            schm_type = str(row[resolved_cols["schm_type"]]).strip().upper()
            
            raw_date = str(row[resolved_cols["acct_cls_date"]]).strip()
            try:
                cls_date = datetime.datetime.strptime(raw_date, "%d.%m.%Y").date()
            except ValueError:
                try:
                    cls_date = pd.to_datetime(raw_date, errors="raise").date()
                except Exception:
                    continue

            unique_dates.add(cls_date)
            records_to_insert.append({
                "sol_id": sol,
                "acct_cls_date": cls_date,
                "schm_type": schm_type
            })

        if not records_to_insert:
            return {"count": 0, "dates": []}

        dates_list = sorted(list(unique_dates))
        with get_db_session() as session:
            session.query(AccountClosureModel).filter(
                AccountClosureModel.acct_cls_date.in_(dates_list)
            ).delete(synchronize_session=False)

            objects = [AccountClosureModel(**rec) for rec in records_to_insert]
            session.bulk_save_objects(objects)
            session.commit()

        return {
            "count": len(records_to_insert),
            "dates": [d.strftime("%Y-%m-%d") for d in dates_list]
        }

    def get_date_limits(self) -> tuple[datetime.date | None, datetime.date | None]:
        """
        Gets min/max dates across both openings and closures.
        """
        with get_db_session() as session:
            min_opn = session.query(func.min(AccountOpeningModel.acct_opn_date)).scalar()
            max_opn = session.query(func.max(AccountOpeningModel.acct_opn_date)).scalar()
            min_cls = session.query(func.min(AccountClosureModel.acct_cls_date)).scalar()
            max_cls = session.query(func.max(AccountClosureModel.acct_cls_date)).scalar()

        dates = [d for d in [min_opn, max_opn, min_cls, max_cls] if d is not None]
        if not dates:
            return None, None
        return min(dates), max(dates)

    def get_performance_data(
        self,
        start_date: datetime.date,
        end_date: datetime.date,
        target_sols: list[int] | None = None,
        sba_thresholds: dict[str, float] | None = None,
        caa_thresholds: dict[str, float] | None = None,
        threshold_field: str = "clr_bal_amt",
        exclude_2nd_4th_sat: bool = True
    ) -> dict:
        """
        Computes detailed branch performance, net openings, and run rates for the given filters.
        Supports population-group specific thresholds.
        """
        # Resolve defaults
        if not sba_thresholds:
            sba_thresholds = {"RURAL": 1000.0, "SEMI URBAN": 1000.0, "URBAN": 1000.0, "METROPOLITAN": 1000.0}
        if not caa_thresholds:
            caa_thresholds = {"RURAL": 5000.0, "SEMI URBAN": 10000.0, "URBAN": 10000.0, "METROPOLITAN": 10000.0}

        sba_thresholds = {str(k).strip().upper(): float(v) for k, v in sba_thresholds.items()}
        caa_thresholds = {str(k).strip().upper(): float(v) for k, v in caa_thresholds.items()}

        # Fetch units master to resolve branch names
        units = self.master_repo.get_by_category("UNIT")
        sol_to_name = {int(u.code): u.name_en for u in units if u.code.isdigit()}
        sol_to_type = {int(u.code): str(u.metadata.get("populationGroup", "RURAL")).strip().upper() for u in units if u.code.isdigit()}

        # Load raw openings and closures from DB
        with get_db_session() as session:
            opn_query = session.query(
                AccountOpeningModel.sol_id,
                AccountOpeningModel.schm_type,
                AccountOpeningModel.clr_bal_amt,
                AccountOpeningModel.average_balance
            ).filter(
                AccountOpeningModel.acct_opn_date >= start_date,
                AccountOpeningModel.acct_opn_date <= end_date
            )
            if target_sols:
                opn_query = opn_query.filter(AccountOpeningModel.sol_id.in_(target_sols))
            openings = [
                {"sol_id": r[0], "schm_type": r[1], "clr_bal_amt": r[2], "average_balance": r[3]}
                for r in opn_query.all()
            ]

            cls_query = session.query(
                AccountClosureModel.sol_id,
                AccountClosureModel.schm_type
            ).filter(
                AccountClosureModel.acct_cls_date >= start_date,
                AccountClosureModel.acct_cls_date <= end_date
            )
            if target_sols:
                cls_query = cls_query.filter(AccountClosureModel.sol_id.in_(target_sols))
            closures = [
                {"sol_id": r[0], "schm_type": r[1]}
                for r in cls_query.all()
            ]

        # Group data by SOL ID
        branch_metrics = {}
        all_sols = set([o["sol_id"] for o in openings] + [c["sol_id"] for c in closures])
        if target_sols:
            all_sols.update(target_sols)

        for sol in all_sols:
            branch_metrics[sol] = {
                "sol": sol,
                "name": sol_to_name.get(sol, f"SOL {sol}"),
                "type": sol_to_type.get(sol, "RURAL"),
                "sba_opened": 0,
                "sba_low_bal": 0,
                "sba_closed": 0,
                "sba_net": 0,
                "sba_run_rate": 0.0,
                "caa_opened": 0,
                "caa_low_bal": 0,
                "caa_closed": 0,
                "caa_net": 0,
                "caa_run_rate": 0.0,
            }

        # Aggregate openings
        for opn in openings:
            sol = opn["sol_id"]
            is_sba = opn["schm_type"] == "SBA"
            is_caa = opn["schm_type"] == "CAA"
            if not (is_sba or is_caa):
                continue

            bal_val = opn.get(threshold_field, 0.0) or 0.0
            sol_type = branch_metrics[sol]["type"]
            
            if is_sba:
                branch_metrics[sol]["sba_opened"] += 1
                sba_th = sba_thresholds.get(sol_type, sba_thresholds.get("RURAL", 1000.0))
                if bal_val < sba_th:
                    branch_metrics[sol]["sba_low_bal"] += 1
            elif is_caa:
                branch_metrics[sol]["caa_opened"] += 1
                caa_th = caa_thresholds.get(sol_type, caa_thresholds.get("RURAL", 10000.0))
                if bal_val < caa_th:
                    branch_metrics[sol]["caa_low_bal"] += 1

        # Aggregate closures
        for cls in closures:
            sol = cls["sol_id"]
            is_sba = cls["schm_type"] == "SBA"
            is_caa = cls["schm_type"] == "CAA"
            if not (is_sba or is_caa):
                continue

            if is_sba:
                branch_metrics[sol]["sba_closed"] += 1
            elif is_caa:
                branch_metrics[sol]["caa_closed"] += 1

        # Calculate working days and months
        working_days = self.calculate_working_days(start_date, end_date, exclude_2nd_4th_sat)
        total_days = (end_date - start_date).days + 1
        months = max(1.0, total_days / 30.0)

        # Compute Net & Run Rates
        for sol, m in branch_metrics.items():
            m["sba_net"] = m["sba_opened"] - m["sba_low_bal"] - m["sba_closed"]
            m["caa_net"] = m["caa_opened"] - m["caa_low_bal"] - m["caa_closed"]

            if working_days > 0:
                m["sba_run_rate"] = m["sba_net"] / working_days
            m["caa_run_rate"] = m["caa_net"] / months

        # Compile summaries
        summary = {
            "sba_opened": sum(m["sba_opened"] for m in branch_metrics.values()),
            "sba_low_bal": sum(m["sba_low_bal"] for m in branch_metrics.values()),
            "sba_closed": sum(m["sba_closed"] for m in branch_metrics.values()),
            "sba_net": sum(m["sba_net"] for m in branch_metrics.values()),
            "caa_opened": sum(m["caa_opened"] for m in branch_metrics.values()),
            "caa_low_bal": sum(m["caa_low_bal"] for m in branch_metrics.values()),
            "caa_closed": sum(m["caa_closed"] for m in branch_metrics.values()),
            "caa_net": sum(m["caa_net"] for m in branch_metrics.values()),
            "working_days": working_days,
            "months": months,
            "sba_run_rate": 0.0,
            "caa_run_rate": 0.0,
        }

        if working_days > 0:
            summary["sba_run_rate"] = summary["sba_net"] / working_days
        summary["caa_run_rate"] = summary["caa_net"] / months

        return {
            "summary": summary,
            "branches": sorted(list(branch_metrics.values()), key=lambda x: x["sba_net"], reverse=True)
        }
