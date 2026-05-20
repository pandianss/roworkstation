from __future__ import annotations
from typing import List, Dict, Any
import datetime
from sqlalchemy.orm import Session
from sqlalchemy import extract, and_
from src.infrastructure.persistence.database import engine, get_db_session
from src.infrastructure.persistence.sqlite_models import Base, BranchVisitModel, MasterRecordModel

# Ensure tables are created
Base.metadata.create_all(engine)

class VisitService:
    def __init__(self, session: Session | None = None):
        self._session = session

    def add_visit(self, sol: int, visit_date: datetime.date, visitor_name: str, 
                  observations: str, advice: str) -> BranchVisitModel:
        if self._session:
            return self._add_visit_tx(self._session, sol, visit_date, visitor_name, observations, advice)
        else:
            with get_db_session() as session:
                new_visit = self._add_visit_tx(session, sol, visit_date, visitor_name, observations, advice)
                session.expunge(new_visit)
                return new_visit

    def _add_visit_tx(self, session: Session, sol: int, visit_date: datetime.date, visitor_name: str, 
                       observations: str, advice: str) -> BranchVisitModel:
        # Get branch name from masters
        branch = session.query(MasterRecordModel).filter(
            and_(MasterRecordModel.category == "UNIT", MasterRecordModel.code == str(sol))
        ).first()
        branch_name = branch.name_en if branch else f"SOL {sol}"

        new_visit = BranchVisitModel(
            sol=sol,
            branch_name=branch_name,
            visit_date=visit_date,
            visitor_name=visitor_name,
            observations=observations,
            advice_to_branch=advice
        )
        session.add(new_visit)
        session.commit()
        return new_visit

    def get_monthly_visits(self, year: int, month: int) -> List[BranchVisitModel]:
        if self._session:
            return self._get_monthly_visits_tx(self._session, year, month)
        else:
            with get_db_session() as session:
                visits = self._get_monthly_visits_tx(session, year, month)
                for v in visits:
                    session.expunge(v)
                return visits

    def _get_monthly_visits_tx(self, session: Session, year: int, month: int) -> List[BranchVisitModel]:
        return session.query(BranchVisitModel).filter(
            and_(
                extract('year', BranchVisitModel.visit_date) == year,
                extract('month', BranchVisitModel.visit_date) == month
            )
        ).order_by(BranchVisitModel.visit_date.asc()).all()

    def delete_visit(self, visit_id: int) -> None:
        if self._session:
            self._delete_visit_tx(self._session, visit_id)
        else:
            with get_db_session() as session:
                self._delete_visit_tx(session, visit_id)

    def _delete_visit_tx(self, session: Session, visit_id: int) -> None:
        visit = session.query(BranchVisitModel).filter(BranchVisitModel.id == visit_id).first()
        if visit:
            session.delete(visit)
            session.commit()

    def update_reply_status(self, visit_id: int, status: bool) -> None:
        if self._session:
            self._update_reply_status_tx(self._session, visit_id, status)
        else:
            with get_db_session() as session:
                self._update_reply_status_tx(session, visit_id, status)

    def _update_reply_status_tx(self, session: Session, visit_id: int, status: bool) -> None:
        visit = session.query(BranchVisitModel).filter(BranchVisitModel.id == visit_id).first()
        if visit:
            visit.reply_received = status
            session.commit()
