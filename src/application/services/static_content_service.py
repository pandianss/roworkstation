from __future__ import annotations

import json
import os
from typing import Any

from src.core.paths import project_path


class StaticContentService:
    """Manages editable static content (business clusters, places to visit)
    stored in data/static_content.json.
    """

    _DATA_PATH = project_path("data", "static_content.json")

    _DEFAULTS: dict[str, Any] = {
        "business_clusters": [],
        "places": [],
    }

    def _load(self) -> dict[str, Any]:
        if not self._DATA_PATH.exists():
            self._save(self._DEFAULTS)
            return dict(self._DEFAULTS)
        try:
            data = json.loads(self._DATA_PATH.read_text(encoding="utf-8"))
            # Ensure both top-level keys exist
            for key, default in self._DEFAULTS.items():
                data.setdefault(key, default)
            return data
        except Exception:
            return dict(self._DEFAULTS)

    def _save(self, data: dict[str, Any]) -> None:
        self._DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._DATA_PATH.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    # ── Public read methods ─────────────────────────────────────────────────

    def get_all(self) -> dict[str, Any]:
        """Return the full static content payload."""
        return self._load()

    def get_clusters(self) -> list[dict]:
        return self._load().get("business_clusters", [])

    def get_places(self) -> list[dict]:
        return self._load().get("places", [])

    # ── Admin write methods ─────────────────────────────────────────────────

    def save_clusters(self, clusters: list[dict]) -> None:
        data = self._load()
        data["business_clusters"] = clusters
        self._save(data)

    def save_places(self, places: list[dict]) -> None:
        data = self._load()
        data["places"] = places
        self._save(data)

    def save_all(self, business_clusters: list[dict], places: list[dict]) -> None:
        self._save({"business_clusters": business_clusters, "places": places})
