from __future__ import annotations

import json

import pandas as pd

from src.core.paths import project_path
from src.domain.schemas import UserAccess
from src.infrastructure.persistence.json_repo import JsonRepository


class AdminService:
    def __init__(self) -> None:
        self.repo = JsonRepository(
            project_path("data", "users.json"),
            [{"username": "admin", "role": "ADMIN", "dept": "ALL"}],
        )
        from src.infrastructure.persistence.master_repository import MasterRepository
        self.master_repo = MasterRepository()

    def list_users(self) -> list[UserAccess]:
        # 1. Get explicit users (Admins, etc.)
        raw_users = self.repo.read()
        staff_records = {s.code: s for s in self.master_repo.get_by_category("STAFF")}
        
        users = []
        for record in raw_users:
            username = str(record.get("username"))
            norm = self._normalize_user(record)
            
            # Enrich from Staff Master if available
            staff = staff_records.get(username)
            if staff:
                meta = staff.metadata or {}
                norm["name"] = staff.name_en
                norm["designation"] = meta.get("designation", "Staff")
                norm["grade"] = meta.get("grade", "N/A")
                if "assigned_branches" not in record:
                    sol = str(meta.get("sol", "ALL"))
                    norm["assigned_branches"] = [sol] if sol != "ALL" else []

            users.append(UserAccess.model_validate(norm))
        
        # 2. Add remaining staff members as default USERS
        user_ids = {u.username for u in users}
        for code, staff in staff_records.items():
            if code not in user_ids:
                meta = staff.metadata or {}
                sol = str(meta.get("sol", "ALL"))
                users.append(UserAccess(
                    username=staff.code,
                    role="USER",
                    dept=meta.get("dept", "ALL"),
                    depts=[meta.get("dept", "ALL")],
                    name=staff.name_en,
                    designation=meta.get("designation", "Staff"),
                    grade=meta.get("grade", "N/A"),
                    assigned_branches=[sol] if sol != "ALL" else []
                ))
        return users

    def get_users_frame(self) -> pd.DataFrame:
        users = [user.model_dump() for user in self.list_users()]
        return pd.DataFrame(users)

    def get_user(self, username: str) -> UserAccess | None:
        # 1. Check explicit users (Admins take precedence)
        users_json = self.repo.read()
        explicit_user = next((u for u in users_json if u.get("username") == username), None)
        
        # 2. Check Staff Master for enrichment
        staff_records = self.master_repo.get_by_category("STAFF")
        staff = next((s for s in staff_records if s.code == username), None)
        
        if explicit_user:
            norm = self._normalize_user(explicit_user)
            if staff:
                meta = staff.metadata or {}
                norm["name"] = staff.name_en
                norm["designation"] = meta.get("designation", "Staff")
                norm["grade"] = meta.get("grade", "N/A")
            return UserAccess.model_validate(norm)
        
        if staff:
            meta = staff.metadata or {}
            sol = str(meta.get("sol", "ALL"))
            return UserAccess(
                    username=staff.code,
                    role="USER",
                    dept=meta.get("dept", "ALL"),
                    depts=[meta.get("dept", "ALL")],
                    name=staff.name_en,
                    designation=meta.get("designation", "Staff"),
                    grade=meta.get("grade", "N/A"),
                    assigned_branches=[sol] if sol != "ALL" else []
                )
        return None

    def add_user(self, username: str, role: str, dept: str = "ALL") -> UserAccess:
        users = self.repo.read()
        record = {"username": username, "role": role, "dept": dept, "depts": [dept]}
        users.append(record)
        self.repo.write(users)
        return UserAccess.model_validate(self._normalize_user(record))

    def update_user(self, username: str, **updates) -> bool:
        users = self.repo.read()
        updated = False
        for record in users:
            if record.get("username") == username:
                record.update(updates)
                if "dept" in record and "depts" not in record:
                    record["depts"] = [record["dept"]]
                updated = True
                break
        if updated:
            self.repo.write(users)
        return updated

    def assign_branches_to_user(self, username: str, branches: list[str]) -> bool:
        users = self.repo.read()
        updated = False
        for record in users:
            if record.get("username") == username:
                record["assigned_branches"] = branches
                updated = True
                break
        if not updated:
            staff = next((s for s in self.master_repo.get_by_category("STAFF") if s.code == username), None)
            role = "USER"
            dept = "ALL"
            if staff:
                meta = staff.metadata or {}
                dept = meta.get("dept", "ALL")
            record = {
                "username": username,
                "role": role,
                "dept": dept,
                "depts": [dept],
                "assigned_branches": branches
            }
            users.append(record)
            updated = True
        
        self.repo.write(users)
        return True

    def _normalize_user(self, record: dict) -> dict:
        normalized = dict(record)
        normalized.setdefault("dept", (normalized.get("depts") or ["ALL"])[0])
        normalized.setdefault("depts", [normalized["dept"]])
        normalized.setdefault("name", normalized["username"])
        normalized.setdefault("assigned_branches", [])
        normalized.setdefault("designation", "System User")
        normalized.setdefault("grade", "N/A")
        normalized.setdefault("rank", 4)
        return normalized
