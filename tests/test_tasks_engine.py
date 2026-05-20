import unittest
from datetime import date
from unittest.mock import MagicMock, patch

from src.application.services.task_service import TaskService
from src.domain.schemas.task import TaskCreate, TaskRead


class TaskServiceTests(unittest.TestCase):
    def test_get_task_summary_counts_open_and_overdue(self):
        service = TaskService(repository=MagicMock())
        service.repository.list_for_user.return_value = [
            TaskRead(id="1", title="Open overdue", dept="CRMD", assigned_to="u1", due_date=date(2024, 1, 1), status="OPEN"),
            TaskRead(id="2", title="Open current", dept="CRMD", assigned_to="u1", due_date=date.today(), status="OPEN"),
            TaskRead(id="3", title="Closed", dept="CRMD", assigned_to="u1", due_date=date.today(), status="CLOSED"),
        ]
        summary = service.get_task_summary("u1")
        self.assertEqual(summary["open"], 2)
        self.assertEqual(summary["overdue"], 1)

    def test_parse_nlp_task_normalizes_invalid_priority_and_due_date(self):
        service = TaskService(repository=MagicMock())
        service.repository.create.side_effect = lambda payload: TaskRead(id="T1", status="OPEN", **payload.model_dump())
        with patch("src.application.services.task_service.LLMClient.generate_json", return_value={"title": "Follow up", "priority": "urgent", "due_date": "bad-date"}):
            task = service.parse_nlp_task("follow up", "user1", "CRMD")
        self.assertEqual(task.priority, "P3")
        self.assertEqual(task.due_date, date.today())
