from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from src.infrastructure.persistence.sqlite_models import CommunicationRequestModel

class CommunicationService:
    def __init__(self, session: Session):
        self.session = session

    def create_request(self, sender_unit: str, sender_name: str, receiver_dept: str, subject: str, message: str, priority: str = "NORMAL") -> CommunicationRequestModel:
        request = CommunicationRequestModel(
            sender_unit=sender_unit,
            sender_name=sender_name,
            receiver_dept=receiver_dept,
            subject=subject,
            message=message,
            priority=priority
        )
        self.session.add(request)
        self.session.commit()
        return request

    def get_requests_for_dept(self, dept: str) -> List[CommunicationRequestModel]:
        return self.session.query(CommunicationRequestModel).filter(
            CommunicationRequestModel.receiver_dept == dept
        ).order_by(CommunicationRequestModel.created_at.desc()).all()

    def get_requests_from_unit(self, unit: str) -> List[CommunicationRequestModel]:
        return self.session.query(CommunicationRequestModel).filter(
            CommunicationRequestModel.sender_unit == unit
        ).order_by(CommunicationRequestModel.created_at.desc()).all()

    def respond_to_request(self, request_id: str, response: str, responded_by: str) -> bool:
        request = self.session.query(CommunicationRequestModel).filter(
            CommunicationRequestModel.id == request_id
        ).first()
        if request:
            request.response_message = response
            request.responded_by = responded_by
            request.responded_at = datetime.now(timezone.utc).replace(tzinfo=None)
            request.status = "RESOLVED"
            self.session.commit()
            return True
        return False

    def update_status(self, request_id: str, status: str) -> bool:
        request = self.session.query(CommunicationRequestModel).filter(
            CommunicationRequestModel.id == request_id
        ).first()
        if request:
            request.status = status
            self.session.commit()
            return True
        return False
