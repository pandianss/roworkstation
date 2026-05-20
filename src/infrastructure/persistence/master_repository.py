from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from src.domain.models.master import MasterRecord
from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.persistence.sqlite_models import MasterRecordModel


class MasterRepository:
    def __init__(self, session_factory=get_db_session) -> None:
        self.session_factory = session_factory

    def get_by_category(self, category: str) -> list[MasterRecord]:
        with self.session_factory() as session:
            records = session.query(MasterRecordModel).filter(
                MasterRecordModel.category == category,
                MasterRecordModel.is_active == True
            ).all()
            return [self._to_domain(r) for r in records]

    def _to_domain(self, model: MasterRecordModel) -> MasterRecord:
        return MasterRecord(
            id=model.id,
            category=model.category,
            code=model.code,
            name_en=model.name_en,
            name_hi=model.name_hi,
            name_local=model.name_local,
            is_active=model.is_active,
            metadata=json.loads(model.metadata_json) if model.metadata_json else {},
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _to_model(self, domain: MasterRecord) -> MasterRecordModel:
        return MasterRecordModel(
            id=domain.id,
            category=domain.category,
            code=domain.code,
            name_en=domain.name_en,
            name_hi=domain.name_hi,
            name_local=domain.name_local,
            is_active=domain.is_active,
            metadata_json=json.dumps(domain.metadata) if domain.metadata else None
        )
    def save(self, domain: MasterRecord) -> None:
        with self.session_factory() as session:
            model = self._to_model(domain)
            session.merge(model)
            session.commit()

    def save_all(self, domains: list[MasterRecord]) -> None:
        with self.session_factory() as session:
            for d in domains:
                model = self._to_model(d)
                session.merge(model)
            session.commit()
