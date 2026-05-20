from __future__ import annotations

from pathlib import Path

from src.core.paths import project_path


class KnowledgeSearchService:
    def __init__(self, knowledge_dir: Path | None = None) -> None:
        self.knowledge_dir = knowledge_dir or project_path("data", "knowledge_docs")

    def search(self, query: str, n_results: int = 5, dept_filter: str | None = None) -> list[dict]:
        if not self.knowledge_dir.exists():
            return []
        term = query.lower().strip()
        matches: list[dict] = []
        for path in self.knowledge_dir.glob("*.txt"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            if term and term not in text.lower():
                continue
            metadata = {"title": path.name, "department": dept_filter or "GENERAL"}
            matches.append({"content": text[:1200], "metadata": metadata})
            if len(matches) >= n_results:
                break
        return matches
