from __future__ import annotations
import yaml
from typing import Dict, List, Any, Optional
from src.core.paths import project_path

class ParameterRegistry:
    """
    Service to provide a central reference point for all project parameters.
    Loads from src/config/parameters.yaml.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ParameterRegistry, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        config_path = project_path("src", "config", "parameters.yaml")
        with open(config_path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f)
        
        self.params = self._config.get("parameters", [])
        self.org = self._config.get("organization", {})
        self.contact = self._config.get("contact", {})
        self.signatories = self._config.get("signatories", {})
        self.nil_sanction_triggers = self._config.get("nil_sanctions", [])
        self.infrastructure = self._config.get("infrastructure", {})
        
        # Build optimized lookups
        self._by_id = {p["id"]: p for p in self.params}
        self._by_mis_col = {p["mis_col"]: p for p in self.params}
        self._by_budget_code = {p["budget_code"]: p for p in self.params}

    def get_all_params(self) -> List[Dict[str, Any]]:
        return self.params

    def get_by_id(self, param_id: str) -> Optional[Dict[str, Any]]:
        return self._by_id.get(param_id)

    def get_by_mis_col(self, mis_col: str) -> Optional[Dict[str, Any]]:
        return self._by_mis_col.get(mis_col)

    def get_by_budget_code(self, budget_code: str) -> Optional[Dict[str, Any]]:
        return self._by_budget_code.get(budget_code)

    def get_mis_to_budget_map(self) -> Dict[str, str]:
        """Returns a map of {MIS_COL: BUDGET_CODE}."""
        return {p["mis_col"]: p["budget_code"] for p in self.params}

    def get_subset_map(self, parent_id: str) -> List[str]:
        """Returns list of MIS columns for a parent ID."""
        p = self.get_by_id(parent_id)
        if not p: return []
        return [self.get_by_id(sid)["mis_col"] for sid in p.get("subsets", []) if self.get_by_id(sid)]

    def get_report_groups(self) -> Dict[str, Dict[str, Any]]:
        """
        Returns groups formatted for PerformanceLetterService.
        { GroupName: { parent: MIS_COL, subsets: [MIS_COL, ...] } }
        """
        groups = {}
        for p in self.params:
            group_name = p.get("report_group")
            if group_name and p.get("is_parent"):
                subsets = []
                for sub_id in p.get("subsets", []):
                    sub_p = self.get_by_id(sub_id)
                    if sub_p:
                        subsets.append(sub_p["mis_col"])
                
                groups[group_name] = {
                    "parent": p["mis_col"],
                    "subsets": subsets
                }
        return groups

    def get_nil_sanction_config(self) -> List[Dict[str, Any]]:
        """Returns the list of products monitored for NIL sanctions."""
        return [t for t in self.nil_sanction_triggers if t.get("active")]

    def get_nil_sanction_map(self) -> Dict[str, str]:
        """Backward compatibility: Returns map {FirstCategory: DisplayName}."""
        mapping = {}
        for t in self.get_nil_sanction_config():
            cats = t.get("target_categories", [])
            if cats:
                mapping[cats[0]] = t["display_name"]
        return mapping

    def get_org_info(self) -> Dict[str, Any]:
        return self.org

    def get_contact_info(self) -> Dict[str, Any]:
        return self.contact

    def get_signatory(self, key: str = "default_rm") -> Dict[str, Any]:
        return self.signatories.get(key, {})

    def get_infrastructure(self) -> Dict[str, Any]:
        return self.infrastructure
