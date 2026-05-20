from __future__ import annotations

import json

from src.application.services.admin_service import AdminService
from src.application.services.task_service import TaskService
from src.core.config.config_loader import get_app_settings
from src.infrastructure.persistence.master_repository import MasterRepository


class GlobalSearchService:
    def __init__(self) -> None:
        self.task_service = TaskService()
        self.admin_service = AdminService()
        self.master_repo = MasterRepository()

    def search(self, query: str, username: str) -> list[dict]:
        term = query.strip().lower()
        if not term:
            return []

        results: list[dict] = []
        for task in self.task_service.get_tasks_for_user(username):
            haystack = " ".join([task.title, task.description or "", task.dept or "", task.status])
            if term in haystack.lower():
                results.append({"type": "Task", "label": task.title, "meta": f"{task.dept} | {task.status}"})

        for user in self.admin_service.list_users():
            haystack = " ".join([user.username, user.name or "", user.designation or ""])
            if term in haystack.lower():
                results.append({"type": "Staff", "label": user.name or user.username, "meta": user.role})

        for branch in self.master_repo.get_by_category("BRANCH"):
            meta = branch.metadata or {}
            haystack = " ".join([branch.code, branch.name_en, str(meta.get("Type", "")), str(meta.get("populationGroup", ""))])
            if term in haystack.lower():
                results.append({"type": "Branch", "label": branch.name_en, "meta": branch.code})

        return results[:12]
