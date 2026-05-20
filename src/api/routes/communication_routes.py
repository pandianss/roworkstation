from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.application.services.communication_service import CommunicationService
from src.infrastructure.persistence.database import get_db_session

router = APIRouter()


class CommunicationRequest(BaseModel):
    sender_unit: str
    sender_name: str = "Branch Manager"
    receiver_dept: str
    subject: str
    message: str
    priority: str = "NORMAL"


@router.post("")
def create_communication(req: CommunicationRequest):
    """Branch submits a request/inquiry to an RO department."""
    try:
        with get_db_session() as session:
            svc = CommunicationService(session)
            svc.create_request(
                sender_unit=req.sender_unit,
                sender_name=req.sender_name,
                receiver_dept=req.receiver_dept,
                subject=req.subject,
                message=req.message,
                priority=req.priority,
            )
        return {"status": "ok", "message": "Request submitted successfully."}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
