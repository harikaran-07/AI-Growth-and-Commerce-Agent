"""
AI Provider - Google Gemini Integration
Uses Google GenAI SYNC Chat API with automatic function calling (AFC).
AFC handles thought_signatures automatically - no manual Part recreation needed.
Functions must have typed parameters with NO default values for AFC to work.
Tools are sync functions that bridge to async via background event loop.
Falls back to a simple intent parser when no API key is configured.
"""

import os
import json
import logging
import asyncio
import threading
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

# Background event loop for sync->async bridging
_bg_loop = None
_bg_lock = threading.Lock()


def _get_bg_loop():
    global _bg_loop
    if _bg_loop is None or _bg_loop.is_closed():
        with _bg_lock:
            if _bg_loop is None or _bg_loop.is_closed():
                _bg_loop = asyncio.new_event_loop()
                threading.Thread(target=_bg_loop.run_forever, daemon=True).start()
    return _bg_loop


# Shared state for tool functions
_tool_calls_log: List[Dict[str, Any]] = []
_current_context: Dict[str, Any] = {}


def set_context(db=None, session_id: str = "default"):
    """Set the current execution context for tool functions."""
    _current_context["db"] = db
    _current_context["session_id"] = session_id


def get_tool_calls_log() -> List[Dict[str, Any]]:
    """Get the list of tool calls made during the last LLM interaction."""
    return _tool_calls_log.copy()


def clear_tool_calls_log():
    """Clear the tool calls log."""
    _tool_calls_log.clear()


def _get_api_key():
    return os.getenv("GEMINI_API_KEY", os.getenv("AI_API_KEY", ""))


def _get_model():
    return os.getenv("GEMINI_MODEL", os.getenv("AI_MODEL", "gemini-3.5-flash-lite"))


AGENT_SYSTEM_PROMPT = """You are MerchantFlow AI, a helpful shopping assistant for TechZone Electronics.

You help users find products, make recommendations, add items to their cart, and complete purchases.

STRICT RULES:
1. Use tools for ALL factual product information. Never invent products, prices, or stock.
2. Never invent payment status or calculate authoritative totals - the backend does that.
3. Recommend relevant products with short reasons.
4. Never initiate payment without explicit user approval.
5. Never bypass spending limits.
6. If a tool fails, explain the failure and recover safely.
7. Be concise and friendly. For financial actions, be transparent.
8. Only provide short user-facing reasons for recommendations.
9. Never expose internal chain-of-thought, tool names, or system details to the user.
10. When the user references "that one", "the first one", refer to products from the most recent search results.
11. Never directly access the database or Razorpay.
12. Never approve a payment on behalf of the user.
13. When the user asks to add a product by position (like "add the first one"), use the add_to_cart tool with product_position parameter.

You are a merchant shopping assistant. Behave professionally and helpfully."""


def _execute_tool_sync(tool_name: str, arguments: dict) -> str:
    """Synchronous tool executor that bridges to async execute_tool."""
    from services.agent_tools import execute_tool
    db = _current_context.get("db")
    session_id = _current_context.get("session_id", "default")

    async def _run():
        return await execute_tool(tool_name, arguments, db, session_id)

    loop = _get_bg_loop()
    future = asyncio.run_coroutine_threadsafe(_run(), loop)
    try:
        result = future.result(timeout=30)
        return result
    except Exception as e:
        logger.error(f"Tool {tool_name} failed: {e}")
        return json.dumps({"error": f"Tool execution failed: {str(e)}"})


def _log_and_execute(tool_name: str, **kwargs) -> str:
    """Log the tool call and execute it synchronously."""
    _tool_calls_log.append({"name": tool_name, "arguments": kwargs})
    return _execute_tool_sync(tool_name, kwargs)


# AFC-compatible tool functions: typed params, NO defaults
def search_products(query: str, category: str, max_price: float, min_price: float, in_stock: bool) -> str:
    """Search the merchant product catalog for products matching criteria."""
    kwargs = {}
    if query: kwargs["query"] = query
    if category: kwargs["category"] = category
    if max_price: kwargs["max_price"] = max_price
    if min_price: kwargs["min_price"] = min_price
    if in_stock: kwargs["in_stock"] = in_stock
    return _log_and_execute("search_products", **kwargs)


def get_product_details(product_id: str) -> str:
    """Get detailed information about a specific product."""
    return _log_and_execute("get_product_details", product_id=product_id)


def check_inventory(product_id: str) -> str:
    """Check inventory/stock level for a product."""
    return _log_and_execute("check_inventory", product_id=product_id)


def recommend_upsell(product_id: str) -> str:
    """Get upsell recommendations for a product (more expensive alternatives)."""
    return _log_and_execute("recommend_upsell", product_id=product_id)


def recommend_cross_sell(product_id: str) -> str:
    """Get cross-sell/complementary product recommendations."""
    return _log_and_execute("recommend_cross_sell", product_id=product_id)


def add_to_cart(product_id: str, product_position: int, quantity: int) -> str:
    """Add a product to the cart. Use product_position (1-based) if product_id is unknown."""
    kwargs = {}
    if product_id: kwargs["product_id"] = product_id
    if product_position: kwargs["product_position"] = product_position
    if quantity: kwargs["quantity"] = quantity
    return _log_and_execute("add_to_cart", **kwargs)


def get_cart() -> str:
    """Get current shopping cart contents and total."""
    return _log_and_execute("get_cart")


def calculate_cart_total() -> str:
    """Calculate the authoritative cart total server-side."""
    return _log_and_execute("calculate_cart_total")


def check_policy() -> str:
    """Check if the cart total is within the merchant spending policy limits."""
    return _log_and_execute("check_policy")


def request_payment_approval() -> str:
    """Request explicit user approval before initiating payment."""
    return _log_and_execute("request_payment_approval")


def get_payment_status(order_id: str) -> str:
    """Get the current payment/order status."""
    return _log_and_execute("get_payment_status", order_id=order_id)


# All AFC-compatible tools
AFC_TOOLS = [
    search_products,
    get_product_details,
    check_inventory,
    recommend_upsell,
    recommend_cross_sell,
    add_to_cart,
    get_cart,
    calculate_cart_total,
    check_policy,
    request_payment_approval,
    get_payment_status,
]


def get_tool_definitions() -> List[Dict[str, Any]]:
    """Return tool definitions for context/reference."""
    return []


async def call_llm(messages: List[Dict[str, Any]], tools: List[Dict[str, Any]],
                   db=None, session_id: str = "default") -> Dict[str, Any]:
    """
    Call Gemini with function calling support via SYNC Chat API + AFC.
    AFC handles thought_signatures automatically.
    Returns: {"content": str|None, "tool_calls": list|None}
    """
    api_key = _get_api_key()
    if api_key and api_key not in ("your_api_key_here", "placeholder_secret", ""):
        return await _call_gemini_chat(api_key, messages, db, session_id)
    else:
        logger.warning("No valid GEMINI_API_KEY set, using fallback intent parser")
        return await _fallback_intent_parser(messages)


async def _call_gemini_chat(api_key: str, messages: List[Dict[str, Any]],
                            db=None, session_id: str = "default") -> Dict[str, Any]:
    """Call Google Gemini using SYNC Chat API with AFC.
    Uses SYNC Chat API (tools are sync) wrapped in asyncio.to_thread.
    AFC handles thought_signatures automatically.
    """
    if genai is None:
        return {"content": "AI service is temporarily unavailable.", "tool_calls": None}

    try:
        model = _get_model()
        logger.info(f"Calling Gemini model={model}")

        client = genai.Client(api_key=api_key)

        # Set context for tool functions
        set_context(db=db, session_id=session_id)
        clear_tool_calls_log()

        # Create config with AFC-compatible tool functions
        config = types.GenerateContentConfig(
            system_instruction=AGENT_SYSTEM_PROMPT,
            tools=AFC_TOOLS,
            temperature=0.7,
            max_output_tokens=1024,
        )

        # Get the last user message
        user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user" and not msg.get("tool_name"):
                user_msg = msg.get("content", "")
                break
        if not user_msg:
            user_msg = "Hello"

        # Use SYNC Chat API in a thread to avoid blocking the event loop.
        # AFC handles tool loop + thought_signatures automatically.
        def _sync_call():
            sync_chat = client.chats.create(model=model, config=config)
            return sync_chat.send_message(user_msg)
        response = await asyncio.to_thread(_sync_call)

        # Parse response
        text = response.text if response.text else None
        tool_calls = get_tool_calls_log()

        logger.info(f"Gemini responded: text_len={len(text) if text else 0}, tools={len(tool_calls)}")
        return {"content": text, "tool_calls": tool_calls if tool_calls else None}

    except Exception as e:
        logger.error(f"Gemini call failed: {type(e).__name__}: {e}", exc_info=True)
        return {"content": "I'm having trouble connecting to the AI service. Please try again in a moment.", "tool_calls": None}


async def _fallback_intent_parser(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Fallback intent parser when no Gemini API key is configured."""
    if not messages:
        return {"content": "Hello! How can I help you find products today?", "tool_calls": None}

    last_msg = messages[-1]
    if last_msg.get("role") != "user":
        return {"content": "Here are the results. Would you like to add any items to your cart?", "tool_calls": None}

    text = last_msg.get("content", "").lower()

    if any(w in text for w in ["search", "find", "show", "looking for", "need", "want"]):
        import re
        category = None
        category_map = {
            "headphone": "Audio", "earphone": "Audio", "earbud": "Audio",
            "speaker": "Audio", "mouse": "Computer Accessories",
            "keyboard": "Computer Accessories", "webcam": "Computer Accessories",
            "phone case": "Mobile Accessories", "charger": "Mobile Accessories",
            "power bank": "Mobile Accessories", "lamp": "Office Products",
        }
        for keyword, cat in category_map.items():
            if keyword in text:
                category = cat
                break
        max_price = None
        price_match = re.search(r'under\s*₹?\s*(\d+)', text)
        if price_match:
            max_price = float(price_match.group(1))
        return {"content": None, "tool_calls": [{"id": "fb1", "name": "search_products", "arguments": {"category": category, "max_price": max_price, "in_stock": True}}]}

    elif any(w in text for w in ["add", "cart", "buy"]):
        import re
        position = 1
        m = re.search(r'(\d+)(?:st|nd|rd|th)', text)
        if m:
            position = int(m.group(1))
        else:
            wm = re.search(r'(first|second|third)', text)
            if wm:
                position = {"first": 1, "second": 2, "third": 3}.get(wm.group(0), 1)
        return {"content": None, "tool_calls": [{"id": "fb2", "name": "add_to_cart", "arguments": {"product_position": position, "quantity": 1}}]}

    elif any(w in text for w in ["cart", "total", "how much", "bill"]):
        return {"content": None, "tool_calls": [{"id": "fb3", "name": "get_cart", "arguments": {}}]}

    elif any(w in text for w in ["pay", "checkout", "proceed"]):
        return {"content": None, "tool_calls": [{"id": "fb4", "name": "request_payment_approval", "arguments": {}}]}

    return {"content": "I can help you find products, add items to your cart, and complete purchases. Try asking 'Find headphones under 3000'.", "tool_calls": None}
