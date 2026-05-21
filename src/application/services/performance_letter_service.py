from __future__ import annotations
import datetime
from typing import Dict, List, Any
import pandas as pd
from src.infrastructure.persistence.budget_repository import BudgetRepository
from src.infrastructure.persistence.advances_repository import AdvancesRepository
from src.application.use_cases.mis.service import MISAnalyticsService
from src.application.services.document import DocumentService
from src.application.services.master_service import MasterService
from src.core.utils.financial_year import get_fy_start

class PerformanceLetterService:
    """Service to generate appreciation and explanation letters based on budget performance."""

    # PARAM_GROUPS defines which MIS columns (ALL UPPERCASE) belong to each letter group.
    # Each group generates one appreciation letter (if ≥100% of budget) and one explanation
    # letter (if <90% of budget) per branch.
    #
    # CASA and TD are separate groups per management preference.
    # Subsets are included so the letter table shows the breakdown.
    # SHG is Core Agri (not MSME). Mudra is the only MSME subset tracked here.
    def __init__(self) -> None:
        from src.core.registry.parameter_service import ParameterRegistry
        self.registry = ParameterRegistry()
        self.PARAM_GROUPS = self.registry.get_report_groups()
        self.NIL_SANCTION_PARAMS = self.registry.get_nil_sanction_map()
        
        self.analytics_service = MISAnalyticsService()
        self.budget_repo = BudgetRepository()
        self.advances_repo = AdvancesRepository()
        self.doc_service = DocumentService()

    def _get_actual(self, row: pd.Series, col: str) -> float:
        """Look up a column value from an MIS row. All enriched columns are now uppercase."""
        val = row.get(col.upper(), 0.0)
        return float(val) if pd.notna(val) else 0.0

    def _get_target(self, param: str, year_month: str, sol: int) -> float:
        """Retrieve budget target for a single param and branch."""
        return self.budget_repo.get_target(param, year_month, sols=[sol])

    def get_branch_performance(self, selected_date: datetime.date) -> List[Dict[str, Any]]:
        """Analyses all branches for budget achievement or decline, group by group."""
        # Determine FY start (Previous March 31st)
        fy_start_date = get_fy_start(selected_date)
        prev_ye_date = fy_start_date - datetime.timedelta(days=1)

        df = self.analytics_service.get_data(start_date=prev_ye_date, end_date=selected_date)
        if df.empty:
            return []

        current_month_df = df[df["DATE"].dt.date == selected_date]
        if current_month_df.empty:
            return []

        prev_ye_df = df[df["DATE"].dt.date == prev_ye_date]

        ym = selected_date.strftime("%Y-%m")
        results = []

        
        master_svc = MasterService()
        units = master_svc.repo.get_by_category("UNIT")
        unit_map = {int(u.code): u.name_en for u in units if u.code.isdigit()}

        for sol in df["SOL"].unique():
            if sol == 3933: continue # Skip RO
            
            branch_data_mask = (df["SOL"] == sol) & (df["DATE"].dt.date == selected_date)
            if not any(branch_data_mask): continue
            row = df[branch_data_mask].iloc[0]

            # Get historical data for this branch
            branch_prev_ye = prev_ye_df[prev_ye_df["SOL"] == sol]
            prev_ye_row = branch_prev_ye.iloc[0] if not branch_prev_ye.empty else None

            branch_result = {
                "sol": sol,
                "branch_name": unit_map.get(int(sol), f"SOL {sol}"),
                "branch_head": master_svc.get_branch_manager(sol),
                "date": selected_date,
                "prev_ye_date": prev_ye_date,
                "groups": {},
            }

            for group_name, cfg in self.PARAM_GROUPS.items():
                parent_col = cfg["parent"]
                all_params = [parent_col] + cfg["subsets"]
                
                # First, gather all stats for this group
                group_stats = []
                has_achievement = False
                has_decline = False

                for param in all_params:
                    actual = self._get_actual(row, param)
                    target = self._get_target(param, ym, int(sol))
                    fy_start_actual = self._get_actual(prev_ye_row, param) if prev_ye_row is not None else 0
                    fy_growth = actual - fy_start_actual

                    # Calculate percentage, handle division by zero
                    if target > 0:
                        pct = (actual / target * 100)
                    else:
                        pct = 0.0

                    entry = {
                        "parameter": param,
                        "actual": actual,
                        "target": target,
                        "variance": actual - target,
                        "pct": pct,
                        "fy_start_actual": fy_start_actual,
                        "fy_growth": fy_growth,
                        "is_parent": (param == parent_col),
                    }
                    group_stats.append(entry)
                    
                    # Trigger logic
                    if pct >= 100 and target > 0:
                        has_achievement = True
                    
                    # Trigger decline if budget shortfall (<90%) OR negative FY growth
                    if (pct < 90 and target > 0) or (fy_growth < 0):
                        has_decline = True
                    
                    if target <= 0 and actual > 0:
                        has_achievement = True

                # If the group has any achievement, include the FULL breakdown in appreciation
                # If the group has any decline, include the FULL breakdown in explanation
                branch_result["groups"][group_name] = {
                    "achievements": group_stats if has_achievement else [],
                    "declines": group_stats if has_decline else [],
                }

            results.append(branch_result)

        return results

    def get_nil_sanction_branches(
        self, selected_date: datetime.date, advances_report_dt: datetime.date
    ) -> List[Dict[str, Any]]:
        """
        Detects branches with NIL sanctions (zero new accounts opened) under Housing and
        Vehicle during the calendar month of selected_date.

        Uses the advances_records table (sourced from the advances portfolio upload).
        An account is counted as a fresh sanction if open_dt falls within the month.

        Args:
            selected_date: The MIS performance date (used to determine the month window).
            advances_report_dt: The report date to query from advances_records.

        Returns:
            List of dicts with sol, branch_name, and nil_params (list of product names).
        """
        month_start = selected_date.replace(day=1)
        if selected_date.month == 12:
            month_end = selected_date.replace(year=selected_date.year + 1, month=1, day=1)
        else:
            month_end = selected_date.replace(month=selected_date.month + 1, day=1)

        adv_df = self.advances_repo.get_records_by_date(advances_report_dt)
        if adv_df.empty:
            return []

        # Filter to accounts opened within the month
        adv_df["open_dt"] = pd.to_datetime(adv_df["open_dt"]).dt.date
        month_sanctions = adv_df[
            (adv_df["open_dt"] >= month_start) & (adv_df["open_dt"] < month_end)
        ]

        # Get all known branches from MIS
        mis_df = self.analytics_service.get_data(start_date=selected_date, end_date=selected_date)
        mis_row = mis_df[mis_df["DATE"].dt.date == selected_date]
        all_sols = [int(s) for s in mis_row["SOL"].unique() if int(s) != 3933]

        results = []
        nil_config = self.registry.get_nil_sanction_config()
        
        for sol in all_sols:
            nil_params = []
            for trigger in nil_config:
                display_name = trigger["display_name"]
                target_cats = trigger.get("target_categories", [])
                target_schemes = trigger.get("target_schemes", [])
                
                # Filter sanctions for this branch and product
                mask = (month_sanctions["branch_code"] == sol)
                if target_cats:
                    mask &= (month_sanctions["l2_sector"].isin(target_cats))
                if target_schemes:
                    mask &= (month_sanctions["schm_code"].isin(target_schemes))
                
                branch_month_sanctions = month_sanctions[mask]
                if len(branch_month_sanctions) == 0:
                    nil_params.append(display_name)

            if nil_params:
                master_svc = MasterService()
                units = master_svc.repo.get_by_category("UNIT")
                unit_map = {int(u.code): u.name_en for u in units if u.code.isdigit()}
                
                branch_name = unit_map.get(int(sol), f"SOL {sol}")
                results.append({
                    "sol": sol,
                    "branch_name": branch_name,
                    "date": selected_date,
                    "nil_params": nil_params,
                })

        return results

    def get_budget_communication_data(self, selected_date: datetime.date) -> List[Dict[str, Any]]:
        """Collects annual targets and historical performance for budget communication."""
        from src.core.utils.financial_year import get_fy_start
        fy_start = get_fy_start(selected_date)
        fy_range = f"{fy_start.year}-{str(fy_start.year+1)[2:]}"
        prev_fy_end_date = (fy_start - datetime.timedelta(days=1))

        df = self.analytics_service.get_data(start_date=prev_fy_end_date, end_date=selected_date)
        if df.empty: return []
        
        # Get branch names from Master Repository
        master_svc = MasterService()
        unit_map = {int(u.code): u.name_en for u in master_svc.repo.get_by_category("UNIT") if u.code.isdigit()}
        
        # Get all branches from latest record
        latest_date = df["DATE"].max()
        unique_sols = df[df["DATE"] == latest_date]["SOL"].unique()
        
        # Create a list of branches with names
        branches_list = []
        for sol in unique_sols:
            branches_list.append({
                "SOL": int(sol),
                "BRANCH": unit_map.get(int(sol), f"SOL {int(sol)}")
            })
        
        # Get all params metadata
        all_params = self.registry.get_all_params()
        
        # Fetch Prev FY End figures for all branches
        prev_fy_df = df[df["DATE"].dt.date == prev_fy_end_date]
        
        results = []
        for row in branches_list:
            sol = row["SOL"]
            if sol == 3933: continue # Skip RO
            
            branch_head = master_svc.get_branch_manager(sol)
            
            # Fetch full monthly grid for this branch
            monthly_df = _self.budget_repo.get_monthly_targets([sol], fy_start)
            if monthly_df.empty: continue
            
            months = list(monthly_df.columns)
            branch_prev_fy = prev_fy_df[prev_fy_df["SOL"] == sol]
            
            # Group by category and handle hierarchy
            categories = ["DEPOSITS", "RETAIL", "MSME", "AGRI", "JEWEL LOAN", "OVERALL"]
            budget_groups = {cat: [] for cat in categories}
            
            # Define specific order for DEPOSITS (Parent first, then subsets)
            deposit_order = ["casa", "sb", "cd", "td", "ret_td"]
            
            # Create a sorted list of params to process
            params_to_process = []
            for p in all_params:
                if p["id"] == "total_retail": continue # Remove Total Retail
                if not p.get("budget_code"): continue
                params_to_process.append(p)
            
            # Sort params logic: Category then custom rule
            def get_sort_key(p):
                cat = p.get("category", "OTHER")
                cat_idx = categories.index(cat) if cat in categories else 99
                
                if cat == "DEPOSITS":
                    sub_idx = deposit_order.index(p["id"]) if p["id"] in deposit_order else 99
                    return (cat_idx, sub_idx)
                
                # For others, parent comes before subsets
                is_parent = p.get("is_parent", False)
                parent_id = p.get("parent_id", "")
                return (cat_idx, 0 if is_parent else 1, parent_id or p["id"])

            params_to_process.sort(key=get_sort_key)
            
            for p in params_to_process:
                cat = p.get("category", "OTHER")
                param_id = p["budget_code"]
                
                if param_id not in monthly_df.index: continue
                
                month_data = monthly_df.loc[param_id]
                prev_val = 0.0
                if not branch_prev_fy.empty and p["mis_col"] in branch_prev_fy.columns:
                    prev_val = float(branch_prev_fy[p["mis_col"]].iloc[0])

                budget_groups[cat].append({
                    "id": p["id"],
                    "display_name": p["display_name"],
                    "is_subset": p.get("parent_id") is not None,
                    "prev_fy_value": prev_val,
                    "monthly_values": month_data.to_dict()
                })

            # Filter out empty categories
            final_groups = {c: v for c, v in budget_groups.items() if v}

            if final_groups:
                results.append({
                    "branch_name": row["BRANCH"],
                    "sol": sol,
                    "fy_range": fy_range,
                    "months": months,
                    "budget_groups": final_groups,
                    "branch_head": branch_head
                })
        
        return results

    def generate_budget_zip(self, budget_data: List[Dict[str, Any]], signatory: Dict[str, Any] | None = None, progress_callback=None, comm_date: str | None = None) -> bytes:
        """Generates a zip of PDF budget communication letters."""
        import io
        import zipfile

        total = len(budget_data)
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for i, branch in enumerate(budget_data):
                if progress_callback:
                    progress_callback((i + 1) / total, f"Generating Budget: {branch['branch_name']}...")

                payload = branch.copy()
                payload["signatory"] = signatory
                payload["date"] = comm_date
                pdf = self.doc_service.generate_budget_communication(payload)
                zf.writestr(f"Budget_Communication_{branch['sol']}.pdf", pdf)
        
        return zip_buffer.getvalue()

    def generate_letters_zip(
        self,
        performance_data: List[Dict[str, Any]],
        nil_sanction_data: List[Dict[str, Any]] | None = None,
        signatory: Dict[str, Any] | None = None,
        progress_callback=None,
        stop_event=None
    ) -> bytes:
        """Generates a zip of PDFs for appreciation and explanation letters. Supports interruption."""
        import io
        import zipfile

        total = len(performance_data)
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:

            # --- Performance letters (achievement / shortfall) ---
            for i, branch in enumerate(performance_data):
                # Check for interruption
                if stop_event and stop_event.is_set():
                    break

                if progress_callback:
                    progress_callback((i + 1) / total, f"Generating Performance: {branch['branch_name']}...")

                for group_name, data in branch["groups"].items():

                    if data["achievements"]:
                        payload = {
                            "branch_name": branch["branch_name"],
                            "sol": branch["sol"],
                            "date": branch["date"],
                            "branch_head": branch.get("branch_head"),
                            "group_name": group_name,
                            "achievements": data["achievements"],
                            "signatory": signatory,
                        }
                        pdf = self.doc_service.generate_performance_appreciation(payload)
                        folder = f"Appreciation_Letters/{group_name.replace(' ', '_')}"
                        zf.writestr(
                            f"{folder}/Appr_{branch['sol']}_{group_name.replace(' ', '_')}.pdf",
                            pdf,
                        )

                    if data["declines"]:
                        payload = {
                            "branch_name": branch["branch_name"],
                            "sol": branch["sol"],
                            "date": branch["date"],
                            "branch_head": branch.get("branch_head"),
                            "group_name": group_name,
                            "declines": data["declines"],
                            "signatory": signatory,
                        }
                        pdf = self.doc_service.generate_explanation_letter(payload)
                        folder = f"Explanation_Letters/{group_name.replace(' ', '_')}"
                        zf.writestr(
                            f"{folder}/Expl_{branch['sol']}_{group_name.replace(' ', '_')}.pdf",
                            pdf,
                        )

            # --- NIL Sanction letters ---
            if nil_sanction_data:
                master_svc = MasterService()
                for branch in nil_sanction_data:
                    payload = {
                        "branch_name": branch["branch_name"],
                        "sol": branch["sol"],
                        "date": branch["date"],
                        "branch_head": master_svc.get_branch_manager(branch["sol"]),
                        "group_name": "NIL Sanction",
                        "declines": [
                            {
                                "parameter": f"{p} — NIL Sanction",
                                "actual": 0,
                                "target": 1,   # Nominal — the point is zero count, not an amount
                                "variance": -1,
                                "pct": 0.0,
                                "is_parent": True,
                            }
                            for p in branch["nil_params"]
                        ],
                    }
                    pdf = self.doc_service.generate_explanation_letter(payload)
                    zf.writestr(
                        f"Explanation_Letters/NIL_Sanction/Expl_{branch['sol']}_NIL_Sanction.pdf",
                        pdf,
                    )

        return zip_buffer.getvalue()

