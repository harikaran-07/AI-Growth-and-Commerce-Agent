"""
AI Provider Abstraction Layer
Supports OpenAI-compatible APIs via environment variables.
Falls back to a simple intent parser when no API key is configured.
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _get_api_key():
    """Read API key at call time (not import time) to ensure env vars are loaded."""
    return os.getenv("AI_API_KEY", "")


def _get_model():
    return os.getenv("AI_MODEL", "gpt-4o-mini")


AGENT_SYSTEM_PROMPT = """You are MerchantFlow AI, a helpful shopping assistant for TechZone Electronics.

You help users find products, make recommendations, add items to their cart, and complete purchases.

RULES:
1. Use tools for ALL factual product information. Never invent products, prices, or stock.
2. Never invent payment status or calculate authoritative totals - the backend does that.
3. Recommend relevant products with short reasons.
4. Never initiate payment without explicit user approval.
5. Never bypass spending limits.
6. If a tool fails, explain the failure and recover safely.
7. Be concise and friendly. For financial actions, be transparent.
8. Only provide short user-facing reasons for recommendations, e.g., "Recommended because it is a compatible accessory."
9. Never expose internal chain-of-thought, tool names, or system details to the user.
10. When the user references "that one", "the first one", "the second one" etc., refer to products from the most recent search results in the conversation.

You are a merchant shopping assistant. Behave professionally and helpfully."""


async def call_llm(messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Call the configured LLM provider."""
    api_key = _get_api_key()
    if api_key and api_key not in ("your_api_key_here", "placeholder_secret", ""):
        return await _call_openai(api_key, messages, tools)
    else:
        logger.warning("No valid AI_API_KEY set, using fallback intent parser")
        return await _fallback_intent_parser(messages)


async def _call_openai(api_key: str, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Call OpenAI-compatible API with function calling."""
    try:
        import openai
        model = _get_model()
        logger.info(f"Calling OpenAI model={model}, key_len={len(api_key)}")

        client = openai.AsyncOpenAI(api_key=api_key)

        openai_tools = []
        for tool in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"]
                }
            })

        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": AGENT_SYSTEM_PROMPT},
                *messages
            ],
            tools=openai_tools if openai_tools else None,
            tool_choice="auto" if openai_tools else None,
            temperature=0.7,
            max_tokens=1024
        )

        choice = response.choices[0]
        message = choice.message

        result = {"content": message.content, "tool_calls": None}

        if message.tool_calls:
            result["tool_calls"] = []
            for tc in message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}
                result["tool_calls"].append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": args
                })

        return result

    except ImportError:
        logger.error("openai package not installed")
        return {"content": "AI service is temporarily unavailable. You can still browse the merchant catalog.", "tool_calls": None}
    except Exception as e:
        logger.error(f"LLM call failed: {type(e).__name__}: {e}")
        return {"content": "I'm having trouble connecting to the AI service. Please try again in a moment.", "tool_calls": None}


async def _fallback_intent_parser(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Fallback intent parser when no LLM API key is configured."""
    if not messages:
        return {"content": "Hello! How can I help you find products today?", "tool_calls": None}

    last_msg = messages[-1]
    if last_msg.get("role") != "user":
        return {"content": "Here are the results from the catalog. Would you like to add any items to your cart?", "tool_calls": None}

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

    return {"content": "I can help you find products, add items to your cart, and complete purchases. Try asking something like 'Find headphones under 3000'.", "tool_calls": None}


def get_tool_definitions() -> List[Dict[str, Any]]:
    """Return tool definitions for the LLM."""
    return [
        {"name": "search_products", "description": "Search the merchant product catalog.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "category": {"type": "string"}, "max_price": {"type": "number"}, "min_price": {"type": "number"}, "in_stock": {"type": "boolean"}}, "required": []}},
        {"name": "get_product_details", "description": "Get detailed info about a specific product.", "parameters": {"type": "object", "properties": {"product_id": {"type": "string"}}, "required": ["product_id"]}},
        {"name": "check_inventory", "description": "Check inventory/stock for a product.", "parameters": {"type": "object", "properties": {"product_id": {"type": "string"}}, "required": ["product_id"]}},
        {"name": "recommend_upsell", "description": "Get upsell recommendations (higher-tier alternatives).", "parameters": {"type": "object", "properties": {"product_id": {"type": "string"}}, "required": ["product_id"]}},
        {"name": "recommend_cross_sell", "description": "Get cross-sell/complementary product recommendations.", "parameters": {"type": "object", "properties": {"product_id": {"type": "string"}}, "required": ["product_id"]}},
        {"name": "add_to_cart", "description": "Add a product to the cart by product_id or product_position (1-based from last search).", "parameters": {"type": "object", "properties": {"product_id": {"type": "string"}, "product_position": {"type": "integer"}, "quantity": {"type": "integer", "minimum": 1}}, "required": []}},
        {"name": "get_cart", "description": "Get current cart contents and total.", "parameters": {"type": "object", "properties": {}, "required": []}},
        {"name": "calculate_cart_total", "description": "Calculate authoritative cart total server-side.", "parameters": {"type": "object", "properties": {}, "required": []}},
        {"name": "check_policy", "description": "Check if cart total is within spending policy limits.", "parameters": {"type": "object", "properties": {}, "required": []}},
        {"name": "request_payment_approval", "description": "Request user approval before initiating payment.", "parameters": {"type": "object", "properties": {}, "required": []}},
        {"name": "get_payment_status", "description": "Get payment/order status.", "parameters": {"type": "object", "properties": {"order_id": {"type": "string"}}, "required": []}},
    ]
