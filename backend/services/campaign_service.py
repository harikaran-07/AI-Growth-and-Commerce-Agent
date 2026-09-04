"""
Campaign Orchestrator Service
=============================
Flow: ANALYZE → OPPORTUNITY DETECTED → CAMPAIGN PROPOSAL → POLICY CHECK →
MERCHANT APPROVAL → EXECUTION → RESULT → AUDIT TRAIL.

- Fully DATA-DRIVEN: opportunities are derived from the deterministic
  synthetic merchant dataset (best sellers, category performance, customer
  funnel, low stock) and the real product catalog (real ids, prices, stock).
- Money-safety: every proposal is EXPLAINABLE (reason/evidence/impact),
  BOUNDED (discount ≤ policy, budget ≤ policy) and GATED (merchant approval).
- Execution is a SYNTHETIC demo result - no fake Razorpay payments, no real
  inventory mutation, clearly labeled "Synthetic Demo Result".
"""
import hashlib
import json
import logging
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.models import Policy, Campaign, Product, ProductRelationship, AuditLog

logger = logging.getLogger(__name__)

# Deterministic seed base for the synthetic simulator
SIM_SEED = 42


# ── Audit helper (campaign events) ─────────────────────────────────────────
async def log_campaign_audit(
    db: AsyncSession,
    campaign_id: str,
    action: str,
    decision: Optional[str] = None,
    policy_result: Optional[str] = None,
    approval_status: Optional[str] = None,
    financial_impact: Optional[float] = None,
    final_status: Optional[str] = None,
    input_data: Optional[str] = None,
):
    audit = AuditLog(
        session_id="campaign",
        user="merchant",
        action=action,
        tool_called="campaign_orchestrator",
        description=f"Campaign {campaign_id[:8]} - {action}",
        input_data=(input_data or "")[:500],
        decision=decision,
        policy_result=policy_result,
        approval_status=approval_status,
        payment_reference=None,
        final_status=final_status,
        event_type="campaign",
        related_entity=campaign_id,
        financial_impact=financial_impact,
        created_at=datetime.now(timezone.utc),
    )
    db.add(audit)
    await db.commit()


# ── Policy helpers ─────────────────────────────────────────────────────────
async def get_default_policy(db: AsyncSession) -> Policy:
    result = await db.execute(select(Policy).limit(1))
    policy = result.scalar_one_or_none()
    if not policy:
        policy = Policy(
            max_transaction_amount=500000,
            max_discount_percentage=10,
            payment_requires_approval=True,
            max_retry_attempts=1,
            max_campaign_budget=100000,
            minimum_margin_percentage=20,
        )
        db.add(policy)
        await db.commit()
        await db.refresh(policy)
    return policy


def _policy_block_reason(policy: Policy, discount: float, budget: float, expected_margin: float) -> Optional[str]:
    """Return a clear reason string when a proposal violates policy, else None."""
    max_discount = float(policy.max_discount_percentage or 10)
    max_budget = float(policy.max_campaign_budget or 100000)
    min_margin = float(policy.minimum_margin_percentage or 0)

    if discount > max_discount + 1e-9:
        return (f"Campaign rejected by policy: discount {discount:.0f}% exceeds "
                f"maximum allowed discount of {max_discount:.0f}%.")
    if budget > max_budget + 1e-9:
        return (f"Campaign rejected by policy: budget ₹{budget:,.0f} exceeds "
                f"maximum campaign budget of ₹{max_budget:,.0f}.")
    # Margin floor only applies to discount actions (informational campaigns
    # such as stockout alerts have no discount and cannot hurt margin).
    if discount > 1e-9 and expected_margin < min_margin - 1e-9:
        return (f"Campaign rejected by policy: expected margin {expected_margin:.1f}% is "
                f"below the minimum required margin of {min_margin:.1f}%.")
    return None


# ── Deterministic numbers from the synthetic dataset ───────────────────────
def _stable(base: float, salt: str, lo: float = 0.85, hi: float = 1.15) -> float:
    """Deterministic small variation around a base value."""
    h = int(hashlib.sha256(salt.encode()).hexdigest(), 16)
    factor = lo + (h % 1000) / 1000.0 * (hi - lo)
    return base * factor


# ── Data-driven opportunity detection ──────────────────────────────────────
async def _load_accessory_candidates(db: AsyncSession) -> List[Product]:
    """Real accessory products from the catalog (cases, cables, chargers, guards, stands)."""
    accessory_subs = ("Cases", "Cables", "Chargers", "Screen Guards", "Adapters",
                      "Hubs", "Laptop Stands", "Car Chargers", "Tablet Covers",
                      "Power Banks", "USB Drives", "Storage", "Cooling Pads",
                      "Backpacks", "Bags", "Wallets")
    result = await db.execute(
        select(Product).where(
            Product.subcategory.in_(accessory_subs),
            Product.stock > 0,
            Product.is_active.isnot(False),
        ).order_by(Product.id).limit(20)
    )
    return list(result.scalars().all())


async def _related_products(db: AsyncSession, product_id: str, rel_type: Optional[str] = None) -> List[Product]:
    q = select(ProductRelationship).where(ProductRelationship.product_id == product_id)
    if rel_type:
        q = q.where(ProductRelationship.relationship_type == rel_type)
    rels = (await db.execute(q)).scalars().all()
    products = []
    for rel in rels:
        p = (await db.execute(select(Product).where(Product.id == rel.related_product_id))).scalar_one_or_none()
        if p and p.stock > 0 and p.is_active:
            products.append(p)
    return products


async def detect_opportunities(db: AsyncSession, ds: Dict[str, Any], policy: Policy) -> List[Dict[str, Any]]:
    """Derive concrete campaign opportunities from the synthetic dataset."""
    opportunities: List[Dict[str, Any]] = []

    best_sellers = ds.get("best_sellers") or []
    top_products = ds.get("top_products") or []
    low_stock = ds.get("low_stock_list") or []
    category_revenue = ds.get("category_revenue") or []
    funnel = ds.get("funnel") or []
    customers_total = float(ds.get("total_customers") or 0)
    avg_order_value = float(ds.get("average_order_value") or 1000)
    checkout_count = 0
    for stage in funnel:
        if stage.get("stage") == "Checkout Started":
            checkout_count = int(stage.get("count") or 0)
    completed = int(ds.get("completed_orders") or 0)

    max_discount = min(float(policy.max_discount_percentage or 10), 10)
    max_budget = float(policy.max_campaign_budget or 100000)
    accessories = await _load_accessory_candidates(db)

    # 1) Cross-sell accessories to a top seller (AOV growth)
    if best_sellers:
        anchor = best_sellers[0]
        pid = anchor.get("id")
        anchor_product = None
        if pid:
            anchor_product = (await db.execute(select(Product).where(Product.id == pid))).scalar_one_or_none()
        target = accessories[0] if accessories else anchor_product
        if anchor_product and target and target.id != anchor_product.id:
            discount = round(min(8.0, max_discount), 1)
            price = float(target.price or 0)
            base_rev = _stable(float(anchor.get("revenue") or 30000) * 0.06, f"xs-{anchor_product.id}-{target.id}")
            budget = min(base_rev * discount / 100.0, max_budget)
            margin = float(target.margin or 50)
            expected_margin = max(margin - discount, 5)
            opportunities.append({
                "name": f"Accessory cross-sell: {anchor_product.name}",
                "objective": "Increase average order value",
                "target_segment": "Customers who purchased " + (anchor_product.category or "this product"),
                "product_ids": [anchor_product.id, target.id],
                "discount_percentage": discount,
                "budget_limit": round(budget, 2),
                "expected_revenue": round(base_rev, 2),
                "expected_profit": round(base_rev * expected_margin / 100.0, 2),
                "expected_margin": expected_margin,
                "reason": f"Customers buying {anchor_product.name} frequently buy compatible accessories. "
                         f"Offer {discount:.0f}% off {target.name} to raise AOV.",
                "evidence": f"Top seller with {anchor.get('units_sold')} units sold; "
                            f"accessory {target.name} priced at ₹{price:,.0f}.",
            })

    # 2) Abandoned-cart recovery campaign
    abandoned = max(checkout_count - completed, 0)
    if abandoned > 0 and customers_total > 0:
        discount = round(min(5.0, max_discount), 1)
        base_rev = _stable(avg_order_value * min(abandoned, 400) * 0.10, f"ab-{abandoned}")
        budget = min(base_rev * discount / 100.0, max_budget)
        opportunities.append({
            "name": "Abandoned cart recovery",
            "objective": "Recover abandoned carts",
            "target_segment": f"{abandoned} shoppers who reached checkout",
            "product_ids": [],
            "discount_percentage": discount,
            "budget_limit": round(budget, 2),
            "expected_revenue": round(base_rev, 2),
            "expected_profit": round(base_rev * 0.28, 2),
            "expected_margin": 28.0,
            "reason": f"{abandoned} carts reached checkout but were not completed. "
                     f"A small incentive recovers a fraction of that revenue.",
            "evidence": f"Funnel: {completed} completed orders vs {checkout_count} checkout starts.",
        })

    # 3) Promote a high-margin / high-revenue category best seller
    if category_revenue:
        top_cat = category_revenue[0]
        in_cat = [p for p in (top_products or []) if p.get("category") == top_cat.get("category")]
        pick = in_cat[0] if in_cat else None
        if pick and pick.get("id"):
            p_obj = (await db.execute(select(Product).where(Product.id == pick["id"]))).scalar_one_or_none()
            if p_obj:
                discount = round(min(8.0, max_discount), 1)
                base_rev = _stable(float(pick.get("revenue") or 20000) * 0.08, f"cat-{pick['id']}")
                budget = min(base_rev * discount / 100.0, max_budget)
                margin = float(p_obj.margin or 45)
                expected_margin = max(margin - discount, 10)
                opportunities.append({
                    "name": f"Boost {p_obj.name}",
                    "objective": "Increase conversion in top category",
                    "target_segment": f"Shoppers browsing {top_cat.get('category')}",
                    "product_ids": [p_obj.id],
                    "discount_percentage": discount,
                    "budget_limit": round(budget, 2),
                    "expected_revenue": round(base_rev, 2),
                    "expected_profit": round(base_rev * expected_margin / 100.0, 2),
                    "expected_margin": expected_margin,
                    "reason": f"{top_cat.get('category')} is the highest-revenue category "
                             f"(₹{float(top_cat.get('revenue') or 0):,.0f}); a limited offer lifts conversion.",
                    "evidence": f"Category revenue leader with {pick.get('units_sold')} units sold.",
                })

    # 4) Inventory / low-stock risk on a fast mover (no discount - informational)
    fast_low = [x for x in low_stock if x.get("sales", 0) > 0]
    if fast_low:
        risk = fast_low[0]
        opportunities.append({
            "name": f"Stockout alert: {risk.get('name', 'fast mover')}",
            "objective": "Reduce stockout risk",
            "target_segment": "Inventory / restock planning",
            "product_ids": [risk.get("id")] if risk.get("id") else [],
            "discount_percentage": 0.0,
            "budget_limit": 0.0,
            "expected_revenue": 0.0,
            "expected_profit": 0.0,
            "expected_margin": 0.0,
            "reason": f"High-selling product has only {risk.get('stock')} units left "
                     f"({risk.get('sales')} units sold in window). Reorder to avoid stockouts.",
            "evidence": f"Inventory status: {risk.get('status') or 'Low'} - stock {risk.get('stock')}.",
        })

    # 5) Suggested-safe discount product (bounded) from top products if we have < 3 above
    if len(opportunities) < 3 and top_products:
        pick = top_products[0]
        p_obj = (await db.execute(select(Product).where(Product.id == pick.get("id")))).scalar_one_or_none()
        if p_obj and float(p_obj.margin or 0) > float(policy.minimum_margin_percentage or 0) + 10:
            discount = round(min(float(policy.max_discount_percentage or 10), 10.0), 1)
            base_rev = _stable(float(pick.get("revenue") or 30000) * 0.05, f"disc-{pick['id']}")
            budget = min(base_rev * discount / 100.0, max_budget)
            expected_margin = max(float(p_obj.margin or 40) - discount, 12)
            opportunities.append({
                "name": f"Limited-time offer: {p_obj.name}",
                "objective": "Increase revenue",
                "target_segment": "All shoppers",
                "product_ids": [p_obj.id],
                "discount_percentage": discount,
                "budget_limit": round(budget, 2),
                "expected_revenue": round(base_rev, 2),
                "expected_profit": round(base_rev * expected_margin / 100.0, 2),
                "expected_margin": expected_margin,
                "reason": f"{p_obj.name} has healthy margin ({float(p_obj.margin or 0):.1f}%); a "
                         f"bounded {discount:.0f}% offer converts lookers into buyers.",
                "evidence": f"Margin {float(p_obj.margin or 0):.1f}%, price ₹{float(p_obj.price or 0):,.0f}.",
            })

    return opportunities[:4]


async def propose_manual_campaign(
    db: AsyncSession,
    name: str,
    objective: str = "Increase revenue",
    target_segment: str = "All shoppers",
    product_ids: Optional[List[str]] = None,
    discount_percentage: float = 0.0,
    budget_limit: float = 0.0,
    expected_margin: float = 30.0,
    reason: str = "",
    evidence: str = "",
) -> Campaign:
    """Create a proposal from explicit merchant/agent inputs (policy-checked).

    Used to demonstrate the money-action boundaries: an out-of-limit request
    (e.g. a 30% discount) is recorded as rejected_by_policy with a clear
    reason and never reaches execution.
    """
    policy = await get_default_policy(db)
    block_reason = _policy_block_reason(policy, discount_percentage, budget_limit, expected_margin)
    sig = f"manual|{name}|{discount_percentage}|{round(budget_limit, 2)}"
    cid = "camp_" + hashlib.sha256(sig.encode()).hexdigest()[:12]

    campaign = Campaign(
        id=cid,
        name=name[:120],
        objective=objective[:120] or "Increase revenue",
        target_segment=target_segment[:120] or "All shoppers",
        product_ids=json.dumps(product_ids or []),
        discount_percentage=discount_percentage,
        budget_limit=budget_limit,
        expected_revenue=0.0,
        expected_profit=0.0,
        expected_margin=expected_margin,
        reason=reason or f"Manual proposal: {discount_percentage:.0f}% discount, budget ₹{budget_limit:,.0f}.",
        evidence=evidence or "Merchant/agent requested action.",
        status="rejected_by_policy" if block_reason else "pending_approval",
        policy_result=block_reason or "pass",
        approval_status="none" if block_reason else "pending",
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)

    await log_campaign_audit(
        db, campaign.id,
        "CAMPAIGN_REJECTED" if block_reason else "CAMPAIGN_PROPOSED",
        decision=f"Manual proposal '{campaign.name}' discount {discount_percentage:.0f}% budget ₹{budget_limit:,.0f}",
        policy_result=block_reason or "pass",
        approval_status=campaign.approval_status,
        final_status=campaign.status,
        input_data=json.dumps({"name": name, "discount": discount_percentage, "budget": budget_limit}),
    )
    if not block_reason:
        await log_campaign_audit(
            db, campaign.id, "CAMPAIGN_APPROVAL_REQUESTED",
            decision="Awaiting merchant approval", approval_status="pending", final_status="pending_approval",
        )
    return campaign


async def propose_campaigns(db: AsyncSession, objective: Optional[str] = None) -> List[Campaign]:
    """Detect opportunities from synthetic data and create bounded proposals."""
    from services.synthetic_data import generate_synthetic_dataset
    ds = await generate_synthetic_dataset(db)
    policy = await get_default_policy(db)
    opportunities = await detect_opportunities(db, ds, policy)

    created = []
    for opp in opportunities:
        if objective and objective.lower() not in (opp["objective"] + " " + opp["name"]).lower():
            continue

        block_reason = _policy_block_reason(
            policy, opp["discount_percentage"], opp["budget_limit"], opp["expected_margin"]
        )
        # Deterministic campaign id from opportunity signature
        sig = f"{opp['name']}|{opp['discount_percentage']}|{round(opp['budget_limit'], 2)}"
        cid = "camp_" + hashlib.sha256(sig.encode()).hexdigest()[:12]

        existing = (await db.execute(select(Campaign).where(Campaign.id == cid))).scalar_one_or_none()
        if existing:
            continue  # avoid duplicate proposals for the same deterministic opportunity

        campaign = Campaign(
            id=cid,
            name=opp["name"],
            objective=opp["objective"],
            target_segment=opp["target_segment"],
            product_ids=json.dumps(opp["product_ids"]),
            discount_percentage=opp["discount_percentage"],
            budget_limit=opp["budget_limit"],
            expected_revenue=opp["expected_revenue"],
            expected_profit=opp["expected_profit"],
            expected_margin=opp["expected_margin"],
            reason=opp["reason"],
            evidence=opp["evidence"],
            status="rejected_by_policy" if block_reason else "pending_approval",
            policy_result=block_reason or "pass",
            approval_status="none" if block_reason else "pending",
        )
        db.add(campaign)
        await db.commit()
        await db.refresh(campaign)

        await log_campaign_audit(
            db, campaign.id,
            "CAMPAIGN_PROPOSED" if not block_reason else "CAMPAIGN_REJECTED",
            decision=f"Proposed '{campaign.name}' discount {campaign.discount_percentage:.0f}% budget ₹{campaign.budget_limit:,.0f}",
            policy_result=block_reason or "pass",
            approval_status=campaign.approval_status,
            final_status=campaign.status,
            input_data=json.dumps({"objective": objective}),
        )
        if not block_reason:
            await log_campaign_audit(
                db, campaign.id, "CAMPAIGN_APPROVAL_REQUESTED",
                decision="Awaiting merchant approval",
                approval_status="pending",
                final_status="pending_approval",
            )
        created.append(campaign)

    return created


async def approve_campaign(db: AsyncSession, campaign_id: str) -> Campaign:
    campaign = (await db.execute(select(Campaign).where(Campaign.id == campaign_id))).scalar_one_or_none()
    if not campaign:
        raise ValueError("Campaign not found")
    if campaign.status != "pending_approval":
        raise ValueError(f"Campaign is not awaiting approval (status: {campaign.status})")

    campaign.status = "approved"
    campaign.approval_status = "approved"
    campaign.policy_result = campaign.policy_result or "pass"
    await db.commit()
    await db.refresh(campaign)
    await log_campaign_audit(
        db, campaign.id, "CAMPAIGN_APPROVED",
        decision=f"Merchant approved campaign '{campaign.name}'",
        policy_result="pass",
        approval_status="approved",
        financial_impact=campaign.budget_limit,
        final_status="approved",
    )
    return campaign


async def reject_campaign(db: AsyncSession, campaign_id: str, reason: Optional[str] = None) -> Campaign:
    campaign = (await db.execute(select(Campaign).where(Campaign.id == campaign_id))).scalar_one_or_none()
    if not campaign:
        raise ValueError("Campaign not found")
    if campaign.status not in ("pending_approval", "approved", "proposed"):
        raise ValueError(f"Campaign cannot be rejected (status: {campaign.status})")

    campaign.status = "rejected"
    campaign.approval_status = "rejected"
    campaign.failure_reason = reason or "Rejected by merchant"
    await db.commit()
    await db.refresh(campaign)
    await log_campaign_audit(
        db, campaign.id, "CAMPAIGN_REJECTED",
        decision=f"Campaign rejected - {campaign.failure_reason}",
        approval_status="rejected",
        final_status="rejected",
    )
    return campaign


# ── Synthetic execution (deterministic, clearly labeled) ───────────────────
async def execute_campaign(
    db: AsyncSession,
    campaign_id: str,
    simulate_inventory_failure: bool = False,
) -> Campaign:
    campaign = (await db.execute(select(Campaign).where(Campaign.id == campaign_id))).scalar_one_or_none()
    if not campaign:
        raise ValueError("Campaign not found")
    if campaign.status != "approved":
        raise ValueError(f"Campaign must be approved before execution (status: {campaign.status})")

    campaign.status = "executing"
    await db.commit()

    # Real inventory check: the promoted product must have enough stock.
    product_ids = json.loads(campaign.product_ids or "[]")
    promo_product = None
    if product_ids:
        promo_product = (await db.execute(
            select(Product).where(Product.id == product_ids[0])
        )).scalar_one_or_none()

    # Determine simulated demand deterministically.
    rng = random.Random(SIM_SEED + int(hashlib.sha256(campaign.id.encode()).hexdigest()[:6], 16))
    customers_targeted = int(rng.randint(600, 1400))
    conv_rate = rng.uniform(0.03, 0.07)
    customers_converted = int(customers_targeted * conv_rate)
    orders = max(customers_converted, 1)
    price = float(promo_product.price or 0) if promo_product else 500
    discount = float(campaign.discount_percentage or 0)
    gross = orders * price
    discount_cost = min(gross * discount / 100.0, float(campaign.budget_limit or gross * discount / 100.0))
    revenue = gross - discount_cost
    profit_margin = float(campaign.expected_margin or 20) / 100.0
    profit = revenue * profit_margin

    # Failure path: insufficient inventory for the simulated demand.
    failed = False
    failure_reason = None
    if promo_product and promo_product.stock <= 0:
        failed, failure_reason = True, (
            "Campaign could not be executed because the promoted product "
            f"'{promo_product.name}' has insufficient inventory (0 units in stock)."
        )
    elif promo_product and promo_product.stock <= 2 and orders > 5:
        failed, failure_reason = True, (
            f"Campaign could not be executed because the promoted product "
            f"'{promo_product.name}' has insufficient inventory "
            f"(only {promo_product.stock} units available - below the safe fulfilment level)."
        )
    if simulate_inventory_failure:
        failed, failure_reason = True, (
            "Synthetic failure demo: campaign execution blocked because the promoted "
            "product has insufficient inventory. No transaction was created and no "
            "stock was deducted."
        )

    if failed:
        campaign.status = "failed"
        campaign.failure_reason = failure_reason
        campaign.result = json.dumps({
            "label": "Synthetic Demo Result",
            "status": "failed",
            "reason": failure_reason,
            "no_transaction_created": True,
            "no_inventory_deducted": True,
        })
        await db.commit()
        await db.refresh(campaign)
        await log_campaign_audit(
            db, campaign.id, "CAMPAIGN_FAILED",
            decision=failure_reason,
            policy_result="pass",
            approval_status="approved",
            final_status="failed",
            input_data=json.dumps({"product_ids": product_ids, "simulate_failure": simulate_inventory_failure}),
        )
        return campaign

    result = {
        "label": "Synthetic Demo Result",
        "simulated": True,
        "status": "completed",
        "customers_targeted": customers_targeted,
        "customers_converted": customers_converted,
        "orders_generated": orders,
        "revenue_generated": round(revenue, 2),
        "discount_cost": round(discount_cost, 2),
        "estimated_profit": round(profit, 2),
        "conversion_uplift": round(conv_rate * 100, 2),
        "product": promo_product.name if promo_product else None,
        "price": price,
        "disclaimer": "Simulated result on synthetic demo data. No real transaction or inventory change occurred.",
    }
    campaign.status = "completed"
    campaign.result = json.dumps(result)
    campaign.executed_at = datetime.now(timezone.utc)
    campaign.failure_reason = None
    await db.commit()
    await db.refresh(campaign)
    await log_campaign_audit(
        db, campaign.id, "CAMPAIGN_EXECUTED",
        decision=f"Executed '{campaign.name}': {orders} orders, revenue ₹{revenue:,.0f}",
        policy_result="pass",
        approval_status="approved",
        financial_impact=round(revenue, 2),
        final_status="completed",
    )
    return campaign
