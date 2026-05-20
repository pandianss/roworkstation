from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonRepository:
    """Generic JSON repository with safe file initialization."""

    def __init__(self, path: Path | str, default: Any) -> None:
        self.path = Path(path)
        self.default = default
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def read(self) -> Any:
        if not self.path.exists():
            self.write(self.default)
        return json.loads(self.path.read_text(encoding="utf-8"))

    def write(self, data: Any) -> Any:
        self.path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        return data
