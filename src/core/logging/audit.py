from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from src.core.paths import project_path


class AuditLogger:
    """Simple file-based audit logger used across services."""

    def __init__(self, file_path: Path | None = None) -> None:
        self.file_path = file_path or project_path("data", "audit.log")
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, user: str, action: str) -> None:
        with self.file_path.open("a", encoding="utf-8") as handle:
            handle.write(f"{datetime.now().isoformat()} | {user} | {action}\n")

    def get_frequent_pages(self, user: str, limit: int = 3) -> list[str]:
        df = self.to_frame()
        if df.empty:
            return []
        
        # Filter by user and "Viewed page" actions
        user_df = df[df["User"] == user]
        page_views = user_df[user_df["Action"].str.contains("Viewed page", na=False)]
        
        if page_views.empty:
            return []
            
        # Extract page names
        page_views["Page"] = page_views["Action"].str.replace("Viewed page ", "", regex=False)
        top_pages = page_views["Page"].value_counts().head(limit).index.tolist()
        return top_pages

    def to_frame(self) -> pd.DataFrame:
        if not self.file_path.exists():
            return pd.DataFrame(columns=["Timestamp", "User", "Action"])

        rows: list[dict[str, str]] = []
        for line in self.file_path.read_text(encoding="utf-8").splitlines():
            parts = line.split(" | ")
            if len(parts) == 3:
                rows.append({"Timestamp": parts[0], "User": parts[1], "Action": parts[2]})
        frame = pd.DataFrame(rows)
        return frame.sort_values("Timestamp", ascending=False) if not frame.empty else frame
