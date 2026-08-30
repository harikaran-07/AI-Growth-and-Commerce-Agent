"""
AI Agent Chat Endpoint
Uses LLM with controlled tool/function calling for agentic commerce.
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

MAX_TOOL_CALLS_PER_TURN = 10


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


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    Main AI agent chat endpoint.
    Uses LLM with tool calling to process user messages.
    """
    session_id = request.session_id
    session_data = get_session_data(session_id)

    # Build conversation history for the LLM
    messages = session_data.get("conversation_history", [])
    messages.append({"role": "user", "content": request.message})

    # Keep conversation history manageable (last 20 messages + system context)
    if len(messages) > 20:
        messages = messages[-20:]

    all_tool_results = []
    all_tool_calls_used = []
    response_text = ""
    products_found = []
    recommendations = []
    cart_info = None
    approval_info = None

    for turn in range(MAX_TOOL_CALLS_PER_TURN):
        try:
            llm_response = await call_llm(messages, get_tool_definitions())
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return ChatResponse(
                message="AI service is temporarily unavailable. You can still browse the merchant catalog at /products.",
                products=[],
                recommendations=[],
                tool_calls=[]
            )

        # If LLM has a text response and no tool calls, we're done
        if llm_response.get("content") and not llm_response.get("tool_calls"):
            response_text = llm_response["content"]
            messages.append({"role": "assistant", "content": response_text})
            break

        # Process tool calls
        tool_calls = llm_response.get("tool_calls", [])
        if not tool_calls:
            response_text = llm_response.get("content", "I'm not sure how to help with that. Try asking about products!")
            messages.append({"role": "assistant", "content": response_text})
            break

        # Add assistant message with tool calls to history
        messages.append({
            "role": "assistant",
            "content": llm_response.get("content"),
            "tool_calls": tool_calls
        })

        for tc in tool_calls:
            tool_name = tc["name"]
            tool_args = tc["arguments"]
            tool_id = tc.get("id", f"call_{tool_name}")

            # Execute the tool on the backend
            tool_result = await execute_tool(tool_name, tool_args, db, session_id)

            all_tool_calls_used.append({
                "tool": tool_name,
                "arguments": tool_args,
                "result_summary": tool_result[:200]
            })

            # Parse tool result and extract data
            try:
                result_data = json.loads(tool_result)
            except json.JSONDecodeError:
                result_data = {"result": tool_result}

            # Collect products for frontend
            if tool_name == "search_products" and "products" in result_data:
                products_found = result_data["products"]

            if tool_name in ("recommend_upsell", "recommend_cross_sell") and "recommendations" in result_data:
                recommendations.extend(result_data["recommendations"])

            if tool_name == "get_cart" and "cart" in result_data:
                cart_info = result_data["cart"]

            if tool_name == "request_payment_approval":
                if "error" in result_data:
                    response_text = result_data["error"]
                else:
                    approval_info = result_data

            # Add tool result to conversation for LLM
            messages.append({
                "role": "tool",
                "tool_call_id": tool_id,
                "content": tool_result
            })

        # If we processed tool calls, ask the LLM to generate a response
        # (will loop back to the top)
        if not response_text:
            continue

    # Save conversation history
    session_data["conversation_history"] = messages

    # If no response text was generated from tools, provide a default
    if not response_text:
        if products_found:
            response_text = f"I found {len(products_found)} product(s) for you. Would you like to add any to your cart?"
        elif recommendations:
            response_text = "Here are some recommendations based on your interests."
        elif cart_info:
            response_text = f"Your cart has {cart_info.get('item_count', 0)} item(s) totaling ₹{cart_info.get('total', 0):.0f}."
        elif approval_info:
            response_text = approval_info.get("message", "Payment approval requested.")
        else:
            response_text = "I've processed your request. Is there anything else I can help with?"

    return ChatResponse(
        message=response_text,
        products=products_found,
        recommendations=recommendations,
        cart=cart_info,
        approval=approval_info,
        payment=None,
        tool_calls=all_tool_calls_used
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

    # Get recommendations for first product
    recommendations = []
    if products:
        rec_result = await execute_tool("recommend_cross_sell", {
            "product_id": products[0]["product_id"]
        }, db, request.session_id)
        rec_data = json.loads(rec_result)
        recommendations = rec_data.get("recommendations", [])

    return SearchResponse(products=products, recommendations=recommendations)


# Keep backward-compatible agent endpoints
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


# Import for backward-compatible approve endpoint
from sqlalchemy import select
