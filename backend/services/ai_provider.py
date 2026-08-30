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

AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")

# Agent system prompt
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
    """
    Call the configured LLM provider.
    Returns: {"content": str or None, "tool_calls": list or None}
    """
    if AI_API_KEY and AI_API_KEY not in ("your_api_key_here", "placeholder_secret", ""):
        return await _call_openai(messages, tools)
    else:
        return await _fallback_intent_parser(messages)


async def _call_openai(messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Call OpenAI-compatible API with function calling."""
    try:
        import openai
        client = openai.AsyncOpenAI(api_key=AI_API_KEY)

        # Convert our tool format to OpenAI format
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
            model=AI_MODEL,
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

        result = {
            "content": message.content,
            "tool_calls": None
        }

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
        logger.warning("openai package not installed, falling back to intent parser")
        return await _fallback_intent_parser(messages)
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return {
            "content": "I'm having trouble processing your request right now. Please try again in a moment.",
            "tool_calls": None
        }


async def _fallback_intent_parser(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Fallback intent parser when no LLM API key is configured.
    Parses common intents from user messages using simple pattern matching.
    Returns tool_calls that mimic what the LLM would return.
    """
    if not messages:
        return {"content": "Hello! How can I help you find products today?", "tool_calls": None}

    last_msg = messages[-1]
    if last_msg.get("role") != "user":
        # If last message is from assistant (tool result), generate a summary response
        return {
            "content": "Here are the results from the catalog. Would you like to add any items to your cart?",
            "tool_calls": None
        }

    text = last_msg.get("content", "").lower()

    # Intent detection
    if any(word in text for word in ["search", "find", "show", "looking for", "need", "want"]):
        tool_calls = []

        # Extract category
        category = None
        category_map = {
            "headphone": "Audio", "earphone": "Audio", "earbud": "Audio",
            "speaker": "Audio", "audio": "Audio",
            "mouse": "Computer Accessories", "keyboard": "Computer Accessories",
            "laptop stand": "Computer Accessories", "cooling pad": "Computer Accessories",
            "webcam": "Computer Accessories", "hub": "Computer Accessories",
            "phone case": "Mobile Accessories", "charger": "Mobile Accessories",
            "power bank": "Mobile Accessories", "screen protector": "Mobile Accessories",
            "mount": "Mobile Accessories",
            "lamp": "Office Products", "desk": "Office Products",
            "monitor stand": "Office Products", "organizer": "Office Products",
            "cable": "Electronics", "ssd": "Electronics", "flash drive": "Electronics",
            "hdmi": "Electronics", "ethernet": "Electronics",
        }
        for keyword, cat in category_map.items():
            if keyword in text:
                category = cat
                break

        # Extract max price
        max_price = None
        import re
        price_match = re.search(r'under\s*₹?\s*(\d+)', text)
        if price_match:
            max_price = float(price_match.group(1))
        # Also check for patterns like "< 3000" or "below 3000"
        price_match2 = re.search(r'(?:under|below|less than|<|<=)\s*(?:₹|rs\.?|inr)?\s*(\d+)', text)
        if price_match2:
            max_price = float(price_match2.group(1))

        tool_calls.append({
            "id": "fallback_001",
            "name": "search_products",
            "arguments": {
                "category": category,
                "max_price": max_price,
                "in_stock": True
            }
        })

        return {"content": None, "tool_calls": tool_calls}

    elif any(word in text for word in ["add", "cart", "buy", "purchase"]):
        # Try to figure out which product to add
        import re
        num_match = re.search(r'(\d+)(?:st|nd|rd|th)', text)
        if not num_match:
            num_match = re.search(r'(?:first|second|third|fourth|fifth)', text)
            if num_match:
                word_to_num = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5}
                position = word_to_num.get(num_match.group(0), 1)
            else:
                position = 1
        else:
            position = int(num_match.group(1))

        tool_calls = [{
            "id": "fallback_002",
            "name": "add_to_cart",
            "arguments": {
                "product_position": position,
                "quantity": 1
            }
        }]
        return {"content": None, "tool_calls": tool_calls}

    elif any(word in text for word in ["recommend", "suggest", "which one", "better", "best"]):
        return {
            "content": "Based on the products shown, I'd recommend the one that best matches your needs and budget. Would you like me to add any of them to your cart?",
            "tool_calls": None
        }

    elif any(word in text for word in ["cart", "total", "how much", "bill"]):
        tool_calls = [{
            "id": "fallback_003",
            "name": "get_cart",
            "arguments": {}
        }]
        return {"content": None, "tool_calls": tool_calls}

    elif any(word in text for word in ["pay", "checkout", "proceed"]):
        tool_calls = [{
            "id": "fallback_004",
            "name": "request_payment_approval",
            "arguments": {}
        }]
        return {"content": None, "tool_calls": tool_calls}

    elif any(word in text for word in ["policy", "limit", "allowed"]):
        tool_calls = [{
            "id": "fallback_005",
            "name": "check_policy",
            "arguments": {}
        }]
        return {"content": None, "tool_calls": tool_calls}

    else:
        return {
            "content": "I can help you find products, add items to your cart, and complete purchases. Try asking something like 'Find headphones under ₹3000' or 'Show me laptop accessories'.",
            "tool_calls": None
        }


def get_tool_definitions() -> List[Dict[str, Any]]:
    """Return tool definitions for the LLM."""
    return [
        {
            "name": "search_products",
            "description": "Search the merchant product catalog. Use this when the user wants to find or browse products. Supports filtering by category and price.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Free text search query"
                    },
                    "category": {
                        "type": "string",
                        "description": "Product category filter (e.g., 'Audio', 'Computer Accessories', 'Mobile Accessories', 'Office Products', 'Electronics')"
                    },
                    "max_price": {
                        "type": "number",
                        "description": "Maximum price filter in INR"
                    },
                    "min_price": {
                        "type": "number",
                        "description": "Minimum price filter in INR"
                    },
                    "in_stock": {
                        "type": "boolean",
                        "description": "Only show in-stock products (default: true)"
                    }
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
                    "product_id": {
                        "type": "string",
                        "description": "The product ID"
                    }
                },
                "required": ["product_id"]
            }
        },
        {
            "name": "check_inventory",
            "description": "Check current inventory/stock for a specific product.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "The product ID"
                    }
                },
                "required": ["product_id"]
            }
        },
        {
            "name": "recommend_upsell",
            "description": "Get upsell recommendations for a product - higher-tier alternatives.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "The product ID to get upsell recommendations for"
                    }
                },
                "required": ["product_id"]
            }
        },
        {
            "name": "recommend_cross_sell",
            "description": "Get cross-sell/complementary product recommendations for a product.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "The product ID to get cross-sell recommendations for"
                    }
                },
                "required": ["product_id"]
            }
        },
        {
            "name": "add_to_cart",
            "description": "Add a product to the user's cart. Use product_id for direct add, or product_position (1-based) to add the Nth product from the most recent search results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "The product ID to add"
                    },
                    "product_position": {
                        "type": "integer",
                        "description": "1-based position of the product from the most recent search results"
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "Quantity to add (default: 1)",
                        "minimum": 1
                    }
                },
                "required": []
            }
        },
        {
            "name": "get_cart",
            "description": "Get the current cart contents and total.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "calculate_cart_total",
            "description": "Calculate the authoritative cart total on the server side.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "check_policy",
            "description": "Check if the current cart total is within the spending policy limits.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "request_payment_approval",
            "description": "Request user approval before initiating payment. This creates an order and an approval request.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "get_payment_status",
            "description": "Get the status of a payment or order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID to check"
                    }
                },
                "required": []
            }
        }
    ]
