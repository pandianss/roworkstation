from __future__ import annotations

import tempfile
from datetime import date
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from src.core.paths import project_path
from src.domain.schemas.task import TaskCreate, TaskRead
from src.infrastructure.persistence.sqlite_models import Base, TaskModel


def _task_sort_key(task: TaskRead) -> tuple:
    return (
        0 if task.status == "OPEN" else 1,
        1 if task.due_date is None else 0,
        task.due_date or date.max,
        -(task.created_at or date.min).toordinal() if hasattr(task.created_at or date.min, "toordinal") else 0,
    )


class TaskRepository:
    def __init__(self) -> None:
        self.engine, self.active_path = self._initialize_engine()
        self.session_factory = sessionmaker(bind=self.engine)

    def _initialize_engine(self):
        default_db_path = project_path("data", "ro_tasks.db")
        fallback_db_path = Path(tempfile.gettempdir()) / "ro_workstation" / "ro_tasks.db"
        for candidate in (default_db_path, fallback_db_path):
            try:
                candidate.parent.mkdir(parents=True, exist_ok=True)
                engine = create_engine(f"sqlite:///{candidate.as_posix()}")
                Base.metadata.create_all(engine)
                return engine, candidate
            except OperationalError:
                continue
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        return engine, Path(":memory:")

    def create(self, payload: TaskCreate) -> TaskRead:
        session = self.session_factory()
        model = TaskModel(**payload.model_dump())
        session.add(model)
        session.commit()
        session.refresh(model)
        session.close()
        return TaskRead.model_validate(model.__dict__)

    def list_for_user(self, username: str, limit: int = 50) -> list[TaskRead]:
        session = self.session_factory()
        models = session.query(TaskModel).filter(TaskModel.assigned_to == username).all()
        session.close()
        tasks = [TaskRead.model_validate(model.__dict__) for model in models]
        return sorted(tasks, key=_task_sort_key)[:limit]

    def update_status(self, task_id: str, status: str) -> bool:
        session = self.session_factory()
        model = session.query(TaskModel).filter(TaskModel.id == task_id).first()
        if not model:
            session.close()
            return False
        model.status = status
        session.commit()
        session.close()
        return True
