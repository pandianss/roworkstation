from __future__ import annotations

from datetime import datetime, timedelta

from src.core.paths import project_path
from src.infrastructure.persistence.json_repo import JsonRepository


class SessionService:
    def __init__(self) -> None:
        self.repo = JsonRepository(project_path("data", "sessions.json"), {})

    def start_session(self, username: str) -> None:
        sessions = self.repo.read()
        sessions[username] = datetime.now().isoformat()
        self.repo.write(sessions)

    def end_session(self, username: str) -> None:
        sessions = self.repo.read()
        sessions.pop(username, None)
        self.repo.write(sessions)

    def is_session_active(self, username: str, timeout_hours: int = 4) -> bool:
        sessions = self.repo.read()
        started_at = sessions.get(username)
        if not started_at:
            return False
        if datetime.now() - datetime.fromisoformat(started_at) < timedelta(hours=timeout_hours):
            return True
        self.end_session(username)
        return False
