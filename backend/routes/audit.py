from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.database import get_db
from models.models import AuditLog
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

class AuditLogResponse(BaseModel):
    id: str
    session_id: Optional[str]
    user: Optional[str]
    action: str
    tool_called: Optional[str]
    input_data: Optional[str]
    decision: Optional[str]
    policy_result: Optional[str]
    approval_status: Optional[str]
    payment_reference: Optional[str]
    final_status: Optional[str]
    created_at: datetime

@router.get("/", response_model=List[AuditLogResponse])
async def get_all_audit_logs(limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    )
    logs = result.scalars().all()
    return [
        AuditLogResponse(
            id=log.id,
            session_id=log.session_id,
            user=log.user,
            action=log.action,
            tool_called=log.tool_called,
            input_data=log.input_data,
            decision=log.decision,
            policy_result=log.policy_result,
            approval_status=log.approval_status,
            payment_reference=log.payment_reference,
            final_status=log.final_status,
            created_at=log.created_at
        ) for log in logs
    ]

@router.get("/{session_id}", response_model=List[AuditLogResponse])
async def get_audit_logs(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AuditLog).where(AuditLog.session_id == session_id).order_by(AuditLog.created_at)
    )
    logs = result.scalars().all()
    return [
        AuditLogResponse(
            id=log.id,
            session_id=log.session_id,
            user=log.user,
            action=log.action,
            tool_called=log.tool_called,
            input_data=log.input_data,
            decision=log.decision,
            policy_result=log.policy_result,
            approval_status=log.approval_status,
            payment_reference=log.payment_reference,
            final_status=log.final_status,
            created_at=log.created_at
        ) for log in logs
    ]
