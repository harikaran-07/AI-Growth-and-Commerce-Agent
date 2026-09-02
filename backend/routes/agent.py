"""
Commerce Assistant Chat Endpoint
Rule-based intent detection with deterministic product search and cart actions.
No external AI API - uses built-in pattern matching and database queries.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from models.database import get_db
from services.ai_provider import call_llm, get_tool_definitions
from services.agent_tools import execute_tool, get_session_data
from pydantic import BaseModel
from typing import List, Optional, Any
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: str


class ChatResponse(BaseModel):
    message: str
    products: List[dict] = []
    recommendations: List[dict] = []
    cart: Optional[dict] = None
    approval: Optional[dict] = None
    payment: Optional[dict] = None
    tool_calls: List[dict] = []
    quick_actions: List[dict] = []


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    Main chat endpoint for the Commerce Assistant.
    Uses rule-based intent detection and deterministic tool execution.
    No external AI API is called.
    """
    session_id = request.session_id
    session_data = get_session_data(session_id)

    # Build conversation history for the LLM
    messages = session_data.get("conversation_history", [])
    messages.append({"role": "user", "content": request.message})

    # Keep conversation history manageable
    if len(messages) > 20:
        messages = messages[-20:]

    all_tool_calls_used = []
    products_found = []
    recommendations = []
    cart_info = None
    approval_info = None

    try:
        # Single call - SYNC Chat API with AFC handles tool loop internally
        llm_response = await call_llm(messages, get_tool_definitions(), db=db, session_id=session_id)
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return ChatResponse(
            message="Chat service is temporarily unavailable. You can still browse the merchant catalog.",
            products=[],
            recommendations=[],
            tool_calls=[],
            quick_actions=[{"label": "Find Products", "message": "Show me popular products"}, {"label": "Help", "message": "Help"}]
        )

    # AFC already executed tools and generated the final response.
    # The response contains both the text and the tool calls log.
    response_text = llm_response.get("content") or ""
    tool_calls = llm_response.get("tool_calls", []) or []

    # Execute ALL tool calls directly and extract results
    # Always execute — don't trust prior execution state
    logger.info(f"[CHAT] Processing {len(tool_calls)} tool calls for session {session_id}")
    for tc in tool_calls:
        tool_name = tc.get("name", "")
        tool_args = tc.get("arguments", {})
        if tool_name:
            try:
                result_str = await execute_tool(tool_name, tool_args, db, session_id)
                result_data = json.loads(result_str)
                tc["result"] = result_data
                logger.info(f"[CHAT] Tool {tool_name} executed, result keys: {list(result_data.keys()) if isinstance(result_data, dict) else type(result_data)}")
            except Exception as e:
                logger.error(f"[CHAT] Tool execution failed ({tool_name}): {e}")
                tc["result"] = {"error": str(e)}
        else:
            logger.warning(f"[CHAT] Skipping tool call with no name: {tc}")

    # Format tool calls for the frontend response
    for tc in tool_calls:
        all_tool_calls_used.append({
            "tool": tc.get("name", "unknown"),
            "arguments": tc.get("arguments", {}),
        })

    # Extract structured data from tool execution results directly
    for tc in tool_calls:
        result = tc.get("result", {})
        if not result or "error" in result:
            logger.info(f"[CHAT] Skipping tool result: error={result.get('error') if isinstance(result, dict) else 'empty'}")
            continue
        tc_name = tc.get("name", "")
        if tc_name == "search_products" and "products" in result:
            products_found = result["products"]
            logger.info(f"[CHAT] Extracted {len(products_found)} products from search")
        elif tc_name == "get_cart" and "cart" in result:
            cart_info = result["cart"]
        elif tc_name == "recommend_cross_sell" and "recommendations" in result:
            recommendations = result["recommendations"]
        elif tc_name == "recommend_upsell" and "recommendations" in result:
            recommendations = result["recommendations"]
    logger.info(f"[CHAT] Final: {len(products_found)} products, response_text empty={not response_text}")



    if not response_text:
        if products_found:
            response_text = f"I found {len(products_found)} product(s) for you. Would you like to add any to your cart?"
        elif recommendations:
            response_text = "Here are some recommendations based on your interests."
        elif cart_info:
            response_text = f"Your cart has {cart_info.get('item_count', 0)} item(s) totaling {cart_info.get('total', 0):.0f}."
        else:
            response_text = "I've processed your request. Is there anything else I can help with?"

    # Save conversation history
    messages.append({"role": "assistant", "content": response_text})
    session_data["conversation_history"] = messages

    # Extract quick_actions from response
    quick_actions = llm_response.get("quick_actions", []) or []

    return ChatResponse(
        message=response_text,
        products=products_found,
        recommendations=recommendations,
        cart=cart_info,
        approval=approval_info,
        payment=None,
        tool_calls=all_tool_calls_used,
        quick_actions=quick_actions
    )


# Backward compatibility: keep /search endpoint
class SearchRequest(BaseModel):
    query: str
    max_price: Optional[float] = None
    category: Optional[str] = None
    session_id: str


class SearchResponse(BaseModel):
    products: List[dict]
    recommendations: List[dict]


@router.post("/search", response_model=SearchResponse)
async def search_products(request: SearchRequest, db: AsyncSession = Depends(get_db)):
    """Backward-compatible search endpoint."""
    result = await execute_tool("search_products", {
        "query": request.query,
        "max_price": request.max_price,
        "category": request.category,
        "in_stock": True
    }, db, request.session_id)

    data = json.loads(result)
    products = data.get("products", [])

    recommendations = []
    if products:
        rec_result = await execute_tool("recommend_cross_sell", {
            "product_id": products[0]["product_id"]
        }, db, request.session_id)
        rec_data = json.loads(rec_result)
        recommendations = rec_data.get("recommendations", [])

    return SearchResponse(products=products, recommendations=recommendations)


# Backward-compatible agent endpoints
class CartRequest(BaseModel):
    session_id: str
    product_ids: List[str]
    quantities: List[int] = []


class CartResponse(BaseModel):
    cart_id: str
    items: List[dict]
    total: float


@router.post("/cart", response_model=CartResponse)
async def create_agent_cart(request: CartRequest, db: AsyncSession = Depends(get_db)):
    """Create a cart with products (backward compatible)."""
    results = []
    total = 0

    for i, pid in enumerate(request.product_ids):
        qty = request.quantities[i] if i < len(request.quantities) else 1
        result = await execute_tool("add_to_cart", {
            "product_id": pid,
            "quantity": qty
        }, db, request.session_id)
        data = json.loads(result)
        if "product" in data:
            results.append(data["product"])
            total += data["product"]["subtotal"]

    cart_id = get_session_data(request.session_id).get("cart_id") or ""

    return CartResponse(cart_id=cart_id, items=results, total=total)


class PaymentRequest(BaseModel):
    cart_id: str
    session_id: str


class PolicyCheckResponse(BaseModel):
    allowed: bool
    reason: str
    total: float
    limit: float


@router.post("/policy-check", response_model=PolicyCheckResponse)
async def check_policy_endpoint(request: PaymentRequest, db: AsyncSession = Depends(get_db)):
    """Check policy (backward compatible)."""
    result = await execute_tool("check_policy", {}, db, request.session_id)
    data = json.loads(result)

    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])

    return PolicyCheckResponse(
        allowed=data["allowed"],
        reason=data["reason"],
        total=data["cart_total"],
        limit=data["spending_limit"]
    )


class ApprovalResponse(BaseModel):
    order_id: str
    approval_id: str
    token: str
    status: str
    message: str


@router.post("/request-approval", response_model=ApprovalResponse)
async def request_approval_endpoint(request: PaymentRequest, db: AsyncSession = Depends(get_db)):
    """Request approval (backward compatible)."""
    result = await execute_tool("request_payment_approval", {}, db, request.session_id)
    data = json.loads(result)

    if "error" in data:
        raise HTTPException(status_code=400, detail=data["error"])

    return ApprovalResponse(
        approval_id=data["approval_id"],
        order_id=data["order_id"],
        token=data["token"],
        status=data["status"],
        message=data["message"]
    )


@router.post("/approve/{approval_id}")
async def approve_payment_endpoint(approval_id: str, db: AsyncSession = Depends(get_db)):
    """Approve payment (backward compatible)."""
    from models.models import Approval, Order
    from sqlalchemy import select

    result = await db.execute(select(Approval).where(Approval.id == approval_id))
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    if approval.status != "pending":
        raise HTTPException(status_code=400, detail="Approval already processed")

    approval.status = "approved"
    approval.approved_by = "user"

    order_result = await db.execute(select(Order).where(Order.id == approval.order_id))
    order = order_result.scalar_one_or_none()
    if order:
        order.status = "approved"

    await db.commit()

    return {"status": "approved", "order_id": approval.order_id}
