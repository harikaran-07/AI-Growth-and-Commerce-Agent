"""
Notifications API - list, mark read, mark all read.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from models.database import get_db
from models.models import Notification
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()


class NotificationResponse(BaseModel):
    id: str
    title: str
    message: Optional[str]
    type: str
    is_read: bool
    related_entity: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=List[NotificationResponse])
async def list_notifications(limit: int = 50, unread_only: bool = False, db: AsyncSession = Depends(get_db)):
    query = select(Notification)
    if unread_only:
        query = query.where(Notification.is_read == False)
    query = query.order_by(Notification.created_at.desc()).limit(limit)
    result = await db.execute(query)
    notifications = result.scalars().all()
    return [
        NotificationResponse(
            id=n.id, title=n.title, message=n.message, type=n.type,
            is_read=n.is_read, related_entity=n.related_entity, created_at=n.created_at
        ) for n in notifications
    ]


@router.get("/unread-count")
async def unread_count(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(func.count(Notification.id)).where(Notification.is_read == False)
    )
    count = result.scalar() or 0
    return {"count": count}


@router.post("/{notification_id}/read")
async def mark_read(notification_id: str, db: AsyncSession = Depends(get_db)):
    from models.models import Notification as NotifModel
    result = await db.execute(select(NotifModel).where(NotifModel.id == notification_id))
    notif = result.scalar_one_or_none()
    if notif:
        notif.is_read = True
        await db.commit()
    return {"status": "ok"}


@router.post("/read-all")
async def mark_all_read(db: AsyncSession = Depends(get_db)):
    from models.models import Notification as NotifModel
    await db.execute(
        update(NotifModel).where(NotifModel.is_read == False).values(is_read=True)
    )
    await db.commit()
    return {"status": "ok"}
