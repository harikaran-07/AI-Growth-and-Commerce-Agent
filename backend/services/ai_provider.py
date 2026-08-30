"""
AI Provider - Google Gemini Integration
Uses the Gemini REST API directly via httpx for full control over
thought_signatures (required by Gemini 3.x models for function calling).
Falls back to a simple intent parser when no API key is configured.
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional
import httpx

logger = logging.getLogger(__name__)

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


def _get_api_key():
    return os.getenv("GEMINI_API_KEY", os.getenv("AI_API_KEY", ""))


def _get_model():
    return os.getenv("GEMINI_MODEL", os.getenv("AI_MODEL", "gemini-3.6-flash"))


GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

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

# Tool declarations for Gemini REST API
GEMINI_TOOL_DECLARATIONS = [
    {
        "name": "search_products",
        "description": "Search the merchant product catalog. Returns matching products with prices and details.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {"type": "STRING", "description": "Search keywords"},
                "category": {"type": "STRING", "description": "Product category filter"},
                "max_price": {"type": "NUMBER", "description": "Maximum price filter"},
                "min_price": {"type": "NUMBER", "description": "Minimum price filter"},
                "in_stock": {"type": "BOOLEAN", "description": "Only show in-stock items"},
            },
        },
    },
    {
        "name": "get_product_details",
        "description": "Get detailed information about a specific product by its ID.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "product_id": {"type": "STRING", "description": "The product ID"},
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "check_inventory",
        "description": "Check inventory/stock for a specific product.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "product_id": {"type": "STRING", "description": "The product ID"},
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "recommend_upsell",
        "description": "Get upsell recommendations for a product (more expensive alternatives).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "product_id": {"type": "STRING", "description": "The product ID"},
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "recommend_cross_sell",
        "description": "Get cross-sell/complementary product recommendations.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "product_id": {"type": "STRING", "description": "The product ID"},
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "add_to_cart",
        "description": "Add a product to the shopping cart by product_id or by product_position (1-based index from search results).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "product_id": {"type": "STRING", "description": "The product ID to add"},
                "product_position": {"type": "INTEGER", "description": "1-based position from search results"},
                "quantity": {"type": "INTEGER", "description": "Quantity to add (default 1)"},
            },
        },
    },
    {
        "name": "get_cart",
        "description": "Get current shopping cart contents and total.",
        "parameters": {"type": "OBJECT", "properties": {}},
    },
    {
        "name": "calculate_cart_total",
        "description": "Calculate the authoritative cart total server-side.",
        "parameters": {"type": "OBJECT", "properties": {}},
    },
    {
        "name": "check_policy",
        "description": "Check if cart total is within the merchant spending policy limits.",
        "parameters": {"type": "OBJECT", "properties": {}},
    },
    {
        "name": "request_payment_approval",
        "description": "Request explicit user approval before initiating payment.",
        "parameters": {"type": "OBJECT", "properties": {}},
    },
    {
        "name": "get_payment_status",
        "description": "Get payment/order status.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "order_id": {"type": "STRING", "description": "The order ID to check"},
            },
        },
    },
]


def get_tool_definitions() -> List[Dict[str, Any]]:
    """Return tool definitions for context/reference."""
    return []


async def call_llm(messages: List[Dict[str, Any]], tools: List[Dict[str, Any]],
                   db=None, session_id: str = "default") -> Dict[str, Any]:
    """
    Call Gemini with function calling via REST API.
    Handles thought_signatures by preserving raw candidate parts.
    Returns: {"content": str|None, "tool_calls": list|None}
    """
    api_key = _get_api_key()
    if api_key and api_key not in ("your_api_key_here", "placeholder_secret", ""):
        return await _call_gemini_rest(api_key, messages, db, session_id)
    else:
        logger.warning("No valid GEMINI_API_KEY set, using fallback intent parser")
        return await _fallback_intent_parser(messages)


async def _call_gemini_rest(api_key: str, messages: List[Dict[str, Any]],
                             db=None, session_id: str = "default") -> Dict[str, Any]:
    """Call Gemini via REST API with manual function calling loop.
    
    This preserves raw candidate parts (including thought_signatures)
    by passing them back as-is in subsequent requests.
    """
    from services.agent_tools import execute_tool

    model = _get_model()
    url = f"{GEMINI_BASE_URL}/models/{model}:generateContent?key={api_key}"
    
    headers = {"Content-Type": "application/json"}
    
    # Build initial contents from conversation history
    contents = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role in ("user", "model"):
            contents.append({
                "role": role,
                "parts": [{"text": content}]
            })
    
    # Ensure last message is from user
    if not contents or contents[-1].get("role") != "user":
        contents.append({
            "role": "user",
            "parts": [{"text": messages[-1].get("content", "Hello")}]
        })

    payload = {
        "contents": contents,
        "systemInstruction": {
            "parts": [{"text": AGENT_SYSTEM_PROMPT}]
        },
        "tools": [{"functionDeclarations": GEMINI_TOOL_DECLARATIONS}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1024,
        },
    }

    all_tool_calls = []
    MAX_ITERATIONS = 10

    async with httpx.AsyncClient(timeout=60.0) as client:
        for iteration in range(MAX_ITERATIONS):
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Gemini API HTTP error: {e.response.status_code}: {e.response.text[:200]}")
                return {"content": "I'm having trouble connecting to the AI service. Please try again in a moment.", "tool_calls": None}
            except Exception as e:
                logger.error(f"Gemini API request failed: {type(e).__name__}: {e}")
                return {"content": "I'm having trouble connecting to the AI service. Please try again in a moment.", "tool_calls": None}

            # Parse candidates
            candidates = data.get("candidates", [])
            if not candidates:
                return {"content": "I couldn't generate a response. Please try again.", "tool_calls": None}

            candidate = candidates[0]
            parts = candidate.get("content", {}).get("parts", [])
            
            # Check for function calls
            function_calls = [p for p in parts if "functionCall" in p]
            text_parts = [p.get("text", "") for p in parts if "text" in p]
            
            if not function_calls:
                # No more tool calls - return final text response
                final_text = "\n".join(text_parts) if text_parts else None
                return {"content": final_text, "tool_calls": all_tool_calls if all_tool_calls else None}

            # Execute tool calls on backend
            # First, add the model's response to contents (preserving raw parts with thought_signatures)
            model_content = {"role": "model", "parts": parts}
            contents.append(model_content)
            
            # Execute each tool and build tool response parts
            tool_parts = []
            for fc in function_calls:
                fc_data = fc["functionCall"]
                tool_name = fc_data["name"]
                tool_args = fc_data.get("args", {})

                all_tool_calls.append({"name": tool_name, "arguments": tool_args})

                # Execute the tool
                try:
                    result_str = await execute_tool(tool_name, tool_args, db, session_id)
                except Exception as e:
                    logger.error(f"Tool {tool_name} failed: {e}")
                    result_str = json.dumps({"error": f"Tool execution failed: {str(e)}"})

                tool_parts.append({
                    "functionResponse": {
                        "name": tool_name,
                        "response": json.loads(result_str) if result_str.strip().startswith("{") or result_str.strip().startswith("[") else {"output": result_str},
                    }
                })

            # Add tool results to contents
            contents.append({"role": "user", "parts": tool_parts})
            
            # Update payload with new contents
            payload["contents"] = contents

        # Max iterations reached
        return {
            "content": "I've processed your request. Is there anything else I can help with?",
            "tool_calls": all_tool_calls if all_tool_calls else None,
        }


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
