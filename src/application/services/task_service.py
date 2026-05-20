from __future__ import annotations

from datetime import date

import pandas as pd

from src.domain.models.enums import TaskPriority
from src.domain.schemas.task import TaskCreate, TaskRead
from src.infrastructure.persistence.task_repository import TaskRepository


class LLMClient:
    def generate_json(self, prompt: str) -> dict:
        return {}


class TaskService:
    def __init__(self, repository: TaskRepository | None = None, llm: LLMClient | None = None) -> None:
        self.repository = repository or TaskRepository()
        self.llm = llm or LLMClient()

    def create_task(self, payload: TaskCreate) -> TaskRead:
        return self.repository.create(payload)

    def get_tasks_for_user(self, username: str, limit: int = 50) -> list[TaskRead]:
        return self.repository.list_for_user(username, limit=limit)

    def update_task_status(self, task_id: str, status: str) -> bool:
        return self.repository.update_status(task_id, status)

    def parse_nlp_task(self, instruction: str, username: str, dept: str) -> TaskRead:
        parsed = self.llm.generate_json(instruction) or {}
        priority = parsed.get("priority", TaskPriority.P3)
        if priority not in {item.value for item in TaskPriority}:
            priority = TaskPriority.P3

        due_date = parsed.get("due_date") or date.today()
        if isinstance(due_date, str):
            try:
                due_date = date.fromisoformat(due_date)
            except ValueError:
                due_date = date.today()

        payload = TaskCreate(
            title=parsed.get("title") or instruction.strip() or "Untitled task",
            description=parsed.get("description", ""),
            dept=parsed.get("dept") or dept,
            assigned_to=parsed.get("assigned_to") or username,
            priority=priority,
            due_date=due_date,
            task_type=parsed.get("task_type", "PERSONAL"),
            source="nlp",
        )
        return self.create_task(payload)

    def get_task_summary(self, username: str) -> dict:
        tasks = self.get_tasks_for_user(username)
        open_tasks = [task for task in tasks if task.status == "OPEN"]
        overdue = [task for task in open_tasks if task.due_date and task.due_date < date.today()]
        return {
            "open": len(open_tasks),
            "overdue": len(overdue),
            "tasks": [task.model_dump() for task in tasks],
        }


    def as_frame(self, username: str) -> pd.DataFrame:
        return pd.DataFrame(task.model_dump() for task in self.get_tasks_for_user(username))
