from __future__ import annotations
import json
import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from src.infrastructure.persistence.sqlite_models import WizardSubmissionModel

from contextlib import contextmanager

class WizardService:
    def __init__(self, session: Session | None = None):
        self._session = session

    @contextmanager
    def _get_session(self):
        if self._session is not None:
            yield self._session
        else:
            from src.infrastructure.persistence.database import get_db_session
            with get_db_session() as s:
                yield s

    def save_submission(self, wizard_type: str, submitted_by: str, content: Dict[str, Any], subject: str = None, ref: str = None) -> WizardSubmissionModel:
        with self._get_session() as session:
            # Prevent double-submit by checking if identical content was just added
            last_sub = session.query(WizardSubmissionModel).filter(
                WizardSubmissionModel.wizard_type == wizard_type,
                WizardSubmissionModel.submitted_by == submitted_by,
                WizardSubmissionModel.subject == subject
            ).order_by(WizardSubmissionModel.created_at.desc()).first()
            
            if last_sub:
                # If created within last 60 seconds and content matches, skip
                now = datetime.datetime.now()
                if (now - last_sub.created_at).total_seconds() < 60:
                    if last_sub.content_json == json.dumps(content, default=str):
                        return last_sub

            new_submission = WizardSubmissionModel(
                wizard_type=wizard_type,
                submitted_by=submitted_by,
                subject=subject,
                reference_no=ref,
                content_json=json.dumps(content, default=str)
            )
            session.add(new_submission)
            session.commit()
            
            # Refresh to attach instance state to a detached object safely
            # or just let it return the detached object since SQLite works
            # but let's make it robust
            session.refresh(new_submission)
            session.expunge(new_submission)
            return new_submission

    def get_submissions(self, wizard_type: str | None = None) -> List[WizardSubmissionModel]:
        with self._get_session() as session:
            query = session.query(WizardSubmissionModel)
            if wizard_type:
                query = query.filter(WizardSubmissionModel.wizard_type == wizard_type)
            results = query.order_by(WizardSubmissionModel.created_at.desc()).all()
            # Expunge all results so they can be read outside of the session
            for r in results:
                session.expunge(r)
            return results

    def get_filtered_submissions(self, search: str | None = None, wizard_type: str | None = None) -> List[WizardSubmissionModel]:
        with self._get_session() as session:
            query = session.query(WizardSubmissionModel)
            if wizard_type and wizard_type != "All":
                query = query.filter(WizardSubmissionModel.wizard_type == wizard_type.lower().replace(' ', '_'))
            
            if search:
                from sqlalchemy import or_
                search_filt = f"%{search}%"
                query = query.filter(or_(
                    WizardSubmissionModel.subject.ilike(search_filt),
                    WizardSubmissionModel.reference_no.ilike(search_filt),
                    WizardSubmissionModel.submitted_by.ilike(search_filt)
                ))
                
            results = query.order_by(WizardSubmissionModel.created_at.desc()).all()
            for r in results:
                session.expunge(r)
            return results

    def delete_submission(self, sub_id: str) -> bool:
        with self._get_session() as session:
            sub = session.query(WizardSubmissionModel).filter(WizardSubmissionModel.id == sub_id).first()
            if sub:
                session.delete(sub)
                session.commit()
                return True
            return False

    def update_submission(self, sub_id: str, content: Dict[str, Any], subject: str = None) -> bool:
        with self._get_session() as session:
            sub = session.query(WizardSubmissionModel).filter(WizardSubmissionModel.id == sub_id).first()
            if sub:
                sub.content_json = json.dumps(content, default=str)
                if subject: sub.subject = subject
                session.commit()
                return True
            return False

    @staticmethod
    def calculate_broken_period_interest(
        principal: float, 
        rate: float, 
        days: int, 
        frequency: str = "SIMPLE"
    ) -> float:
        """
        Logic from BrokenPeriodInterestForm.tsx
        """
        if days <= 0 or rate <= 0 or principal <= 0:
            return 0.0
            
        if frequency == "SIMPLE":
            # P * R * D / 365
            return round((principal * (rate / 100) * days) / 365, 2)
        
        # Compound logic: Maturity Value = P * (1 + r/n)^(n*t)
        # Interest = Maturity Value - Principal
        t = days / 365
        n_map = {"QUARTERLY": 4, "MONTHLY": 12, "HALFYEARLY": 2, "ANNUALLY": 1}
        n = n_map.get(frequency, 1)
        
        maturity_value = principal * ((1 + (rate / (100 * n))) ** (n * t))
        return round(maturity_value - principal, 2)
