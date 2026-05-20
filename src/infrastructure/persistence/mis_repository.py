from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.paths import project_path
from src.infrastructure.persistence.sqlite_models import Base, IngestedFileModel, MISRecordModel


class MISRepository:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or project_path("data", "mis_store.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(f"sqlite:///{self.db_path.as_posix()}")
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)

    def is_file_ingested(self, filename: str) -> bool:
        session = self.session_factory()
        exists = session.query(IngestedFileModel).filter(IngestedFileModel.filename == filename).first() is not None
        session.close()
        return exists

    def mark_file_ingested(self, filename: str) -> None:
        session = self.session_factory()
        try:
            existing = session.query(IngestedFileModel).filter(IngestedFileModel.filename == filename).first()
            if existing:
                from datetime import datetime, timezone
                existing.ingested_at = datetime.now(timezone.utc).replace(tzinfo=None)
            else:
                session.add(IngestedFileModel(filename=filename))
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete_ingested_file(self, filename: str) -> bool:
        """Removes the record of an ingested file from the tracking table."""
        session = self.session_factory()
        try:
            target = session.query(IngestedFileModel).filter(IngestedFileModel.filename == filename).first()
            if target:
                session.delete(target)
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()

    def save_records(self, records: list[dict]) -> None:
        session = self.session_factory()
        try:
            objects = []
            valid_keys = set(MISRecordModel.__table__.columns.keys())
            unique_dates = set()
            
            for record in records:
                normalized = {key.lower().replace(" ", "_"): value for key, value in record.items()}
                filtered = {key: value for key, value in normalized.items() if key in valid_keys}
                
                # Robust date validation
                if "date" in filtered and filtered["date"] is not None and not pd.isna(filtered["date"]):
                    if hasattr(filtered["date"], "date"):
                        filtered["date"] = filtered["date"].date()
                    unique_dates.add(filtered["date"])
                    objects.append(MISRecordModel(**filtered))
            
            # Only proceed if we have valid objects with valid dates
            if unique_dates:
                # Filter unique_dates to ensure no None/NaN slipped through
                clean_dates = [d for d in unique_dates if d is not None]
                if clean_dates:
                    session.query(MISRecordModel).filter(MISRecordModel.date.in_(clean_dates)).delete(synchronize_session=False)
            
            if objects:
                session.bulk_save_objects(objects)
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_available_dates(self) -> list:
        session = self.session_factory()
        dates = session.query(MISRecordModel.date).distinct().all()
        session.close()
        return sorted([d[0] for d in dates if d[0]])

    def get_available_sols(self) -> list:
        session = self.session_factory()
        sols = session.query(MISRecordModel.sol).distinct().all()
        session.close()
        return sorted([int(s[0]) for s in sols if s[0] is not None])

    def load_frame(self, start_date=None, end_date=None) -> pd.DataFrame:
        session = self.session_factory()
        query = session.query(MISRecordModel)
        
        if start_date:
            query = query.filter(MISRecordModel.date >= start_date)
        if end_date:
            query = query.filter(MISRecordModel.date <= end_date)
            
        frame = pd.read_sql(query.statement, self.engine)
        session.close()
        return frame
