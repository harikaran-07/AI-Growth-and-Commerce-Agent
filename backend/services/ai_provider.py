"""
AI Provider - Google Gemini Integration
Uses Google GenAI SDK for LLM-powered agent with function/tool calling.
Falls back to a simple intent parser when no API key is configured.
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _get_api_key():
    return os.getenv("GEMINI_API_KEY", os.getenv("AI_API_KEY", ""))


def _get_model():
    return os.getenv("GEMINI_MODEL", os.getenv("AI_MODEL", "gemini-2.5-flash"))


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
8. Only provide short user-facing reasons for recommendations, e.g., "Recommended because it is a compatible accessory."
9. Never expose internal chain-of-thought, tool names, or system details to the user.
10. When the user references "that one", "the first one", "the second one" etc., refer to products from the most recent search results in the conversation.
11. Never directly access the database or Razorpay.
12. Never approve a payment on behalf of the user.

You are a merchant shopping assistant. Behave professionally and helpfully."""


async def call_llm(messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Call Gemini with function calling support."""
    api_key = _get_api_key()
    if api_key and api_key not in ("your_api_key_here", "placeholder_secret", ""):
        return await _call_gemini(api_key, messages, tools)
    else:
        logger.warning("No valid GEMINI_API_KEY set, using fallback intent parser")
        return await _fallback_intent_parser(messages)


async def _call_gemini(api_key: str, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Call Google Gemini API with function calling."""
    try:
        from google import genai
        from google.genai import types

        model = _get_model()
        logger.info(f"Calling Gemini model={model}, key_len={len(api_key)}")

        client = genai.Client(api_key=api_key)

        # Convert tools to Gemini format
        gemini_tools = []
        if tools:
            func_declarations = []
            for tool in tools:
                # Convert our schema to Gemini Schema
                properties = {}
                for pname, pdef in tool.get("parameters", {}).get("properties", {}).items():
                    type_map = {
                        "string": types.Type.STRING,
                        "number": types.Type.NUMBER,
                        "integer": types.Type.INTEGER,
                        "boolean": types.Type.BOOLEAN,
                    }
                    properties[pname] = types.Schema(
                        type=type_map.get(pdef.get("type", "string"), types.Type.STRING),
                        description=pdef.get("description", "")
                    )

                required_fields = tool.get("parameters", {}).get("required", [])

                func_declarations.append(types.FunctionDeclaration(
                    name=tool["name"],
                    description=tool.get("description", ""),
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties=properties,
                        required=required_fields if required_fields else None
                    )
                ))
            gemini_tools = [types.Tool(function_declarations=func_declarations)]

        # Build contents from conversation history
        contents = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "assistant":
                contents.append(types.Content(
                    role="model",
                    parts=[types.Part(text=content or "")]
                ))
            elif role == "user":
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part(text=content)]
                ))
            elif role == "tool":
                # Tool results - include as function response
                tool_call_id = msg.get("tool_call_id", "")
                try:
                    result_data = json.loads(content)
                except json.JSONDecodeError:
                    result_data = {"result": content}
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_function_response(
                        name=tool_call_id.split("_")[0] if "_" in tool_call_id else "tool",
                        response=result_data
                    )]
                ))

        if not contents:
            contents = [types.Content(role="user", parts=[types.Part(text="Hello")])]

        # Make the API call
        config = types.GenerateContentConfig(
            tools=gemini_tools if gemini_tools else None,
            system_instruction=AGENT_SYSTEM_PROMPT,
            temperature=0.7,
            max_output_tokens=1024
        )

        response = await client.aio.models.generate_content(
            model=model,
            contents=contents,
            config=config
        )

        # Parse response
        result = {"content": response.text if response.text else None, "tool_calls": None}

        if response.function_calls:
            result["tool_calls"] = []
            for fc in response.function_calls:
                result["tool_calls"].append({
                    "id": f"call_{fc.name}",
                    "name": fc.name,
                    "arguments": dict(fc.args) if fc.args else {}
                })

        return result

    except ImportError:
        logger.error("google-genai package not installed")
        return {"content": "AI service is temporarily unavailable. You can still browse the catalog.", "tool_calls": None}
    except Exception as e:
        logger.error(f"Gemini call failed: {type(e).__name__}: {e}")
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


def get_tool_definitions() -> List[Dict[str, Any]]:
    """Return tool definitions for the LLM."""
    return [
        {"name": "search_products", "description": "Search the merchant product catalog. Use when the user wants to find or browse products.", "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "Free text search query"}, "category": {"type": "string", "description": "Product category (Audio, Computer Accessories, Mobile Accessories, Office Products, Electronics)"}, "max_price": {"type": "number", "description": "Maximum price in INR"}, "min_price": {"type": "number", "description": "Minimum price in INR"}, "in_stock": {"type": "boolean", "description": "Only show in-stock products"}}, "required": []}},
        {"name": "get_product_details", "description": "Get detailed info about a specific product by ID.", "parameters": {"type": "object", "properties": {"product_id": {"type": "string", "description": "The product ID"}}, "required": ["product_id"]}},
        {"name": "check_inventory", "description": "Check inventory/stock for a product.", "parameters": {"type": "object", "properties": {"product_id": {"type": "string"}}, "required": ["product_id"]}},
        {"name": "recommend_upsell", "description": "Get upsell recommendations (higher-tier alternatives).", "parameters": {"type": "object", "properties": {"product_id": {"type": "string"}}, "required": ["product_id"]}},
        {"name": "recommend_cross_sell", "description": "Get cross-sell/complementary product recommendations.", "parameters": {"type": "object", "properties": {"product_id": {"type": "string"}}, "required": ["product_id"]}},
        {"name": "add_to_cart", "description": "Add a product to the cart by product_id or product_position (1-based from last search).", "parameters": {"type": "object", "properties": {"product_id": {"type": "string"}, "product_position": {"type": "integer"}, "quantity": {"type": "integer"}}, "required": []}},
        {"name": "get_cart", "description": "Get current cart contents and total.", "parameters": {"type": "object", "properties": {}, "required": []}},
        {"name": "calculate_cart_total", "description": "Calculate authoritative cart total server-side.", "parameters": {"type": "object", "properties": {}, "required": []}},
        {"name": "check_policy", "description": "Check if cart total is within spending policy limits.", "parameters": {"type": "object", "properties": {}, "required": []}},
        {"name": "request_payment_approval", "description": "Request user approval before initiating payment.", "parameters": {"type": "object", "properties": {}, "required": []}},
        {"name": "get_payment_status", "description": "Get payment/order status.", "parameters": {"type": "object", "properties": {"order_id": {"type": "string"}}, "required": []}},
    ]
