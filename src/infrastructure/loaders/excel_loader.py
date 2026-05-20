import pandas as pd
from pathlib import Path
from typing import Optional

class ExcelLoader:
    def load(self, path: Path) -> pd.DataFrame:
        if not path.exists():
            raise FileNotFoundError(f"Excel file not found at {path}")
        return pd.read_excel(path)

    def load_mis_sheet(self, path: Path) -> pd.DataFrame:
        df = self.load(path)
        # Add basic validation or cleaning here
        return df
