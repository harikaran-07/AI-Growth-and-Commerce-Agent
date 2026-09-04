"""
Campaign Orchestrator API
=========================
POST   /api/campaigns/propose        → analyze synthetic data & create proposals
POST   /api/campaigns/{id}/approve   → merchant approval
POST   /api/campaigns/{id}/reject    → merchant rejection
POST   /api/campaigns/{id}/execute   → synthetic execution (approved only)
GET    /api/campaigns                → list campaigns (status filter)
GET    /api/campaigns/{id}           → campaign detail
"""
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db
from models.models import Campaign
from services.campaign_service import (
    propose_campaigns, propose_manual_campaign, approve_campaign,
    reject_campaign, execute_campaign,
)

router = APIRouter()


def _campaign_dict(c: Campaign) -> dict:
    product_ids = json.loads(c.product_ids or "[]")
    result = {}
    if c.result:
        try:
            result = json.loads(c.result)
        except (ValueError, TypeError):
            result = {}
    return {
        "campaign_id": c.id,
        "name": c.name,
        "objective": c.objective,
        "target_segment": c.target_segment,
        "product_ids": product_ids,
        "discount_percentage": c.discount_percentage or 0,
        "budget_limit": c.budget_limit or 0,
        "expected_revenue": c.expected_revenue or 0,
        "expected_profit": c.expected_profit or 0,
        "expected_margin": c.expected_margin or 0,
        "reason": c.reason,
        "evidence": c.evidence,
        "status": c.status,
        "policy_result": c.policy_result,
        "approval_status": c.approval_status,
        "failure_reason": c.failure_reason,
        "result": result,
        "label": c.label,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "executed_at": c.executed_at.isoformat() if c.executed_at else None,
    }


class ProposeRequest(BaseModel):
    objective: Optional[str] = None
    # Manual proposal fields (used to demonstrate the policy guard)
    name: Optional[str] = None
    target_segment: Optional[str] = None
    discount_percentage: Optional[float] = None
    budget_limit: Optional[float] = None
    expected_margin: Optional[float] = None
    reason: Optional[str] = None
    product_ids: Optional[list] = None


class ExecuteRequest(BaseModel):
    simulate_inventory_failure: Optional[bool] = False


class RejectRequest(BaseModel):
    reason: Optional[str] = None


@router.get("/")
@router.get("")
async def list_campaigns(
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    query = select(Campaign).order_by(Campaign.created_at.desc()).limit(limit)
    if status:
        query = select(Campaign).where(Campaign.status == status).order_by(Campaign.created_at.desc()).limit(limit)
    result = await db.execute(query)
    campaigns = result.scalars().all()
    return [_campaign_dict(c) for c in campaigns]


@router.get("/{campaign_id}")
async def get_campaign(campaign_id: str, db: AsyncSession = Depends(get_db)):
    campaign = (await db.execute(select(Campaign).where(Campaign.id == campaign_id))).scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return _campaign_dict(campaign)


@router.post("/propose")
async def propose(request: Optional[ProposeRequest] = None, db: AsyncSession = Depends(get_db)):
    """Propose campaigns.

    - With a manual `name`/`discount_percentage` payload → policy-checked
      explicit proposal (demonstrates the money-action boundaries, e.g. a 30%
      discount is rejected with a clear reason).
    - Without → analyze the synthetic merchant dataset and propose the
      data-driven opportunities detected.
    """
    try:
        if request and request.name:
            campaigns = [await propose_manual_campaign(
                db,
                name=request.name,
                objective=request.objective or "Increase revenue",
                target_segment=request.target_segment or "All shoppers",
                product_ids=request.product_ids or [],
                discount_percentage=float(request.discount_percentage or 0),
                budget_limit=float(request.budget_limit or 0),
                expected_margin=float(request.expected_margin or 30),
                reason=request.reason or "",
            )]
        else:
            campaigns = await propose_campaigns(db, request.objective if request else None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    if not campaigns:
        raise HTTPException(
            status_code=409,
            detail="No new campaign opportunities detected - existing proposals cover the current opportunities.",
        )
    return {
        "proposed": [_campaign_dict(c) for c in campaigns],
        "count": len(campaigns),
    }


@router.post("/{campaign_id}/approve")
async def approve(campaign_id: str, db: AsyncSession = Depends(get_db)):
    try:
        campaign = await approve_campaign(db, campaign_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _campaign_dict(campaign)


@router.post("/{campaign_id}/reject")
async def reject(campaign_id: str, request: Optional[RejectRequest] = None, db: AsyncSession = Depends(get_db)):
    try:
        campaign = await reject_campaign(db, campaign_id, request.reason if request else None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _campaign_dict(campaign)


@router.post("/{campaign_id}/execute")
async def execute(campaign_id: str, request: Optional[ExecuteRequest] = None, db: AsyncSession = Depends(get_db)):
    try:
        campaign = await execute_campaign(
            db, campaign_id,
            simulate_inventory_failure=bool(request.simulate_inventory_failure) if request else False,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _campaign_dict(campaign)
