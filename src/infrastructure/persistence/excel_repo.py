from __future__ import annotations

from pathlib import Path

import pandas as pd


class ExcelRepository:
    """Excel reader abstraction for MIS ingestion."""

    def read(self, path: Path) -> pd.DataFrame:
        return pd.read_excel(path)
