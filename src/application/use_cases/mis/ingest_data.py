from pathlib import Path
from src.infrastructure.loaders.excel_loader import ExcelLoader
from src.infrastructure.persistence.mis_repo import MISRepository
from src.core.config.loader import settings

class MISIngestionUseCase:
    def __init__(self, loader: ExcelLoader, repo: MISRepository):
        self.loader = loader
        self.repo = repo

    def execute(self):
        mis_dir = settings.mis_dir
        archive_dir = mis_dir / "archive"
        archive_dir.mkdir(exist_ok=True)
        
        new_files = list(mis_dir.glob("*.xlsx"))
        for f_path in new_files:
            try:
                df = self.loader.load_mis_sheet(f_path)
                # Processing and saving logic here
                # ...
                # Move to archive
                f_path.rename(archive_dir / f_path.name)
            except Exception as e:
                print(f"Error ingesting {f_path}: {e}")
