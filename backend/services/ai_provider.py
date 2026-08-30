"""
AI Provider - Google Gemini Integration
Uses Google GenAI SDK with manual tool calling loop.
Falls back to a simple intent parser when no API key is configured.
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional

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
13. When the user asks to add a product by position (like "add the first one" or "add the second"), use the add_to_cart tool with product_position parameter.

You are a merchant shopping assistant. Behave professionally and helpfully."""


# Tool definitions in Gemini function_declarations format
GEMINI_TOOLS = [
    {
        "name": "search_products",
        "description": "Search the merchant product catalog. Returns matching products with details.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query text, e.g. 'wireless headphones'"},
                "category": {"type": "string", "description": "Product category, e.g. 'Audio', 'Computer Accessories'"},
                "max_price": {"type": "number", "description": "Maximum price filter in INR"},
                "min_price": {"type": "number", "description": "Minimum price filter in INR"},
                "in_stock": {"type": "boolean", "description": "Only show in-stock items"}
            },
            "required": []
        }
    },
    {
        "name": "get_product_details",
        "description": "Get detailed information about a specific product by its ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "The product ID"}
            },
            "required": ["product_id"]
        }
    },
    {
        "name": "check_inventory",
        "description": "Check inventory/stock availability for a product.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "The product ID to check"}
            },
            "required": ["product_id"]
        }
    },
    {
        "name": "recommend_upsell",
        "description": "Get upsell (higher-end) recommendations for a product.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "The product ID to get upsell for"}
            },
            "required": ["product_id"]
        }
    },
    {
        "name": "recommend_cross_sell",
        "description": "Get cross-sell (complementary) product recommendations.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "The product ID to get cross-sell for"}
            },
            "required": ["product_id"]
        }
    },
    {
        "name": "add_to_cart",
        "description": "Add a product to the shopping cart. Use product_id if known, or product_position if user referenced by position (e.g. 'the first one').",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "Product ID to add"},
                "product_position": {"type": "integer", "description": "Position in search results (1-based)"},
                "quantity": {"type": "integer", "description": "Number to add (default 1)"}
            },
            "required": []
        }
    },
    {
        "name": "get_cart",
        "description": "Get current shopping cart contents and total.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "calculate_cart_total",
        "description": "Calculate the authoritative cart total server-side.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "check_policy",
        "description": "Check if the cart total is within the merchant's spending policy limits.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "request_payment_approval",
        "description": "Request explicit user approval before initiating a payment.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_payment_status",
        "description": "Get the status of a payment/order.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order ID to check"}
            },
            "required": []
        }
    },
]


def get_tool_definitions() -> List[Dict[str, Any]]:
    """Return tool definitions for the LLM."""
    return GEMINI_TOOLS


def _map_type(type_str: str):
    """Map JSON Schema types to Gemini Schema types."""
    mapping = {
        "string": types.Type.STRING,
        "number": types.Type.NUMBER,
        "integer": types.Type.INTEGER,
        "boolean": types.Type.BOOLEAN,
        "object": types.Type.OBJECT,
        "array": types.Type.ARRAY,
    }
    return mapping.get(type_str, types.Type.STRING)


def _build_gemini_contents(messages: List[Dict[str, Any]]) -> List:
    """Convert message history to Gemini contents format."""
    contents = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        tool_calls = msg.get("tool_calls")

        if role == "user":
            # Check if this is a function response (tool result)
            if msg.get("tool_name"):
                try:
                    parsed = json.loads(content) if isinstance(content, str) else content
                except (json.JSONDecodeError, TypeError):
                    parsed = {"result": content}
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_function_response(
                        name=msg["tool_name"],
                        response=parsed
                    )]
                ))
            else:
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=content or "")]
                ))
        elif role == "assistant":
            parts = []
            if content:
                parts.append(types.Part.from_text(text=str(content)))
            if tool_calls:
                for tc in tool_calls:
                    args = {}
                    for k, v in tc.get("arguments", {}).items():
                        args[k] = v
                    parts.append(types.Part.from_function_call(
                        name=tc["name"],
                        args=args
                    ))
            if parts:
                contents.append(types.Content(role="model", parts=parts))

    return contents


async def call_llm(messages: List[Dict[str, Any]], tools: List[Dict[str, Any]],
                   db=None, session_id: str = "default") -> Dict[str, Any]:
    """
    Call Gemini with function calling support.
    Returns: {"content": str|None, "tool_calls": list|None}
    """
    api_key = _get_api_key()
    if api_key and api_key not in ("your_api_key_here", "placeholder_secret", ""):
        return await _call_gemini(api_key, messages, db, session_id)
    else:
        logger.warning("No valid GEMINI_API_KEY set, using fallback intent parser")
        return await _fallback_intent_parser(messages)


async def _call_gemini(api_key: str, messages: List[Dict[str, Any]],
                       db=None, session_id: str = "default") -> Dict[str, Any]:
    """Call Google Gemini using generate_content for manual tool loop."""
    if genai is None:
        return {"content": "AI service is temporarily unavailable. google-genai package not installed.", "tool_calls": None}

    try:
        model = _get_model()
        logger.info(f"Calling Gemini model={model}")

        client = genai.Client(api_key=api_key)

        # Build Gemini contents from message history
        contents = _build_gemini_contents(messages)

        if not contents:
            return {"content": "Hello! How can I help you find products today?", "tool_calls": None}

        # Create tool declarations
        function_declarations = []
        for tool_def in GEMINI_TOOLS:
            function_declarations.append(
                types.FunctionDeclaration(
                    name=tool_def["name"],
                    description=tool_def["description"],
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            k: types.Schema(
                                type=_map_type(v["type"]),
                                description=v.get("description", "")
                            ) for k, v in tool_def["parameters"].get("properties", {}).items()
                        },
                        required=tool_def["parameters"].get("required", [])
                    )
                )
            )

        config = types.GenerateContentConfig(
            system_instruction=AGENT_SYSTEM_PROMPT,
            tools=[types.Tool(function_declarations=function_declarations)],
            temperature=0.7,
            max_output_tokens=1024
        )

        response = await client.aio.models.generate_content(
            model=model,
            contents=contents,
            config=config
        )

        # Extract response
        result = {"content": None, "tool_calls": None}

        if response.candidates and response.candidates[0].content:
            parts = response.candidates[0].content.parts
            has_function_calls = False
            text_parts = []

            for part in parts:
                if hasattr(part, "function_call") and part.function_call:
                    has_function_calls = True
                    if result["tool_calls"] is None:
                        result["tool_calls"] = []
                    fc = part.function_call
                    args = {}
                    if fc.args:
                        for k, v in fc.args.items():
                            args[k] = v
                    result["tool_calls"].append({
                        "id": f"call_{fc.name}_{len(result['tool_calls'])}",
                        "name": fc.name,
                        "arguments": args
                    })
                elif hasattr(part, "text") and part.text:
                    text_parts.append(part.text)

            if text_parts:
                result["content"] = "\n".join(text_parts)

            # If there are function calls, prefer them over text
            if has_function_calls:
                result["content"] = result["content"] or None

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
