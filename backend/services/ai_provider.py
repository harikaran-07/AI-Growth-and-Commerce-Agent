"""
AI Provider - Supports Gemini with dual-key failover and rule-based fallback.
Gemini API Key 1 → Key 2 → Rule-based fallback.
Keys are NEVER exposed to frontend.
"""

import os
import json
import logging
import time
import random
from typing import Any, Dict, List, Optional
import httpx

logger = logging.getLogger(__name__)

# Detect provider
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").lower()

# Gemini API keys - ONLY from backend env vars, never exposed to frontend
GEMINI_KEY_1 = os.getenv("GEMINI_API_KEY_1", os.getenv("GEMINI_API_KEY", ""))
GEMINI_KEY_2 = os.getenv("GEMINI_API_KEY_2", "")
GEMINI_KEYS = [k for k in [GEMINI_KEY_1, GEMINI_KEY_2] if k and k not in ("your_api_key_here", "placeholder_secret", "")]

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_MODEL = os.getenv("AI_MODEL", "gemini-2.0-flash")

# Retry config
MAX_RETRIES = 2
RETRY_DELAY_BASE = 1.0
RETRY_DELAY_MAX = 5.0

# Track which key is exhausted (in-memory, per-process)
_exhausted_keys: set = set()
_key_cooldowns: dict = {}  # key -> timestamp when cooldown expires


def _get_available_keys() -> List[str]:
    """Get Gemini API keys that are not currently exhausted."""
    now = time.time()
    available = []
    for key in GEMINI_KEYS:
        if key in _exhausted_keys:
            # Check if cooldown has expired
            cooldown_until = _key_cooldowns.get(key, 0)
            if now >= cooldown_until:
                _exhausted_keys.discard(key)
                available.append(key)
            # else still exhausted
        else:
            available.append(key)
    return available


def _mark_key_exhausted(key: str):
    """Mark a key as exhausted with exponential cooldown."""
    _exhausted_keys.add(key)
    # Cooldown: 5 minutes
    _key_cooldowns[key] = time.time() + 300
    logger.warning(f"Gemini API key ...{key[-6:]} marked as exhausted (cooldown 5min)")


def _is_quota_error(status_code: int, response_text: str) -> bool:
    """Check if error is a quota/rate-limit error."""
    if status_code == 429:
        return True
    text_lower = response_text.lower()
    quota_indicators = [
        "resource_exhausted",
        "quota exceeded",
        "rate limit",
        "429",
        "too many requests",
        "quota",
        "exceeded",
    ]
    return any(ind in text_lower for ind in quota_indicators)


AGENT_SYSTEM_PROMPT = """You are the AI Growth and Commerce Agent, a friendly shopping and commerce assistant.

You help customers discover, compare, and buy products naturally. You also help merchants analyze their store performance.

CAPABILITIES:
1. Product search and recommendations
2. Cart management
3. Compare products
4. Answer questions about products, prices, stock
5. Guide customers through purchase flow
6. Sales analysis and recommendations
7. Inventory alerts

CONVERSATION STYLE:
- Be warm, friendly, and helpful like a knowledgeable store clerk
- Use natural language: 'Sure! I can help you find the right product.'
- Never say 'Based on database records...' — say 'Here are the best options for you.'
- When recommending products, present them clearly with name, price, and stock
- Ask follow-up questions to understand needs: budget, preferences, use case
- If a product is low in stock, mention it
- Always offer to add products to cart

RULES:
1. Use tools for ALL factual product information. NEVER invent products, prices, or stock.
2. NEVER invent payment status or calculate authoritative totals.
3. Recommend relevant products with short, friendly reasons.
4. Never initiate payment without explicit user approval.
5. Be concise and friendly.
6. Never expose internal tool names, system details, or API keys.
7. Product names should be displayed cleanly without Markdown formatting.
8. If you don't have enough data, say so honestly.
9. Never fabricate business metrics.
10. Always use the clean product name from the catalog, not formatted versions."""


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "Search the merchant product catalog.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search keywords"},
                    "category": {"type": "string", "description": "Product category filter"},
                    "max_price": {"type": "number", "description": "Maximum price filter"},
                    "min_price": {"type": "number", "description": "Minimum price filter"},
                    "in_stock": {"type": "boolean", "description": "Only show in-stock items"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_details",
            "description": "Get detailed information about a specific product.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string", "description": "The product ID"},
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_inventory",
            "description": "Check inventory/stock for a specific product.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string", "description": "The product ID"},
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recommend_upsell",
            "description": "Get upsell recommendations for a product.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string", "description": "The product ID"},
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recommend_cross_sell",
            "description": "Get cross-sell/complementary product recommendations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string", "description": "The product ID"},
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_cart",
            "description": "Add a product to the shopping cart.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string", "description": "The product ID to add"},
                    "product_position": {"type": "integer", "description": "1-based position from search results"},
                    "quantity": {"type": "integer", "description": "Quantity to add (default 1)"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_cart",
            "description": "Get current shopping cart contents and total.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_merchant_analytics",
            "description": "Get merchant business analytics: revenue, profit, top sellers, slow movers, low stock, and sales trends.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_sales_recommendations",
            "description": "Get AI-powered sales growth recommendations based on real merchant data.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


def get_tool_definitions() -> List[Dict[str, Any]]:
    """Return tool definitions for context/reference."""
    return TOOL_DEFINITIONS


async def generate_ai_response(prompt: str, options: dict = None) -> str:
    """
    Centralized AI response generator with dual-key failover.
    
    Flow: Key 1 → Key 2 → Rule-based fallback
    Never exposes API keys. Never crashes.
    """
    available_keys = _get_available_keys()
    
    if not available_keys:
        logger.warning("No Gemini API keys available, using rule-based fallback")
        return _rule_based_fallback(prompt)
    
    last_error = None
    
    for key in available_keys:
        for attempt in range(MAX_RETRIES):
            try:
                model = GEMINI_MODEL
                url = f"{GEMINI_BASE_URL}/models/{model}:generateContent?key={key}"
                
                headers = {"Content-Type": "application/json"}
                payload = {
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                    "systemInstruction": {"parts": [{"text": AGENT_SYSTEM_PROMPT}]},
                    "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1024},
                }
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(url, headers=headers, json=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            text_parts = [p.get("text", "") for p in parts if "text" in p]
                            if text_parts:
                                return "\n".join(text_parts)
                        return "I couldn't generate a response. Please try again."
                    
                    if _is_quota_error(response.status_code, response.text):
                        logger.warning(f"Gemini key ...{key[-6:]} quota/rate limited (attempt {attempt+1})")
                        _mark_key_exhausted(key)
                        last_error = f"Quota exceeded on key ...{key[-6:]}"
                        break  # Try next key
                    
                    # Non-quota error - retry once
                    if attempt == 0:
                        logger.warning(f"Gemini API error {response.status_code}, retrying...")
                        time.sleep(RETRY_DELAY_BASE)
                        continue
                    
                    last_error = f"Gemini API error: {response.status_code}"
                    break  # Move to next key
                    
            except httpx.TimeoutException:
                logger.warning(f"Gemini timeout for key ...{key[-6:]}")
                if attempt == 0:
                    time.sleep(RETRY_DELAY_BASE)
                    continue
                last_error = "Timeout"
                break
            except Exception as e:
                logger.error(f"Gemini error: {type(e).__name__}: {e}")
                last_error = str(e)
                break
    
    # All keys failed - use rule-based fallback
    logger.warning(f"All Gemini keys failed ({last_error}), using rule-based fallback")
    return _rule_based_fallback(prompt)


def _rule_based_fallback(prompt: str) -> str:
    """Deterministic rule-based response when AI is unavailable."""
    prompt_lower = prompt.lower()
    
    if any(w in prompt_lower for w in ["what should i sell", "what to sell", "recommend", "suggest"]):
        return ("I recommend checking your top-selling products and promoting them. "
                "Focus on products with high margins and good sales velocity. "
                "Check the Analytics page for detailed insights.")
    
    if any(w in prompt_lower for w in ["low stock", "restock", "inventory"]):
        return ("Check your Products page for items with low stock. "
                "Products with fewer than 10 units should be restocked soon.")
    
    if any(w in prompt_lower for w in ["profit", "margin", "revenue"]):
        return ("Visit the Analytics page to see your revenue, profit, and margin data. "
                "The dashboard shows real-time metrics from your orders.")
    
    if any(w in prompt_lower for w in ["slow", "not selling", "underperforming"]):
        return ("Check the Dashboard for slow-moving products. "
                "Consider promotions or bundles for products with low sales velocity.")
    
    if any(w in prompt_lower for w in ["bundle", "cross-sell", "upsell"]):
        return ("Look at products in the same category for natural bundles. "
                "Cross-selling complementary products can increase your average order value.")
    
    return ("The AI assistant is temporarily unavailable due to API limits. "
            "You can still browse products, manage your cart, and view analytics. "
            "Please try again in a few minutes.")


async def call_llm(messages: List[Dict[str, Any]], tools: List[Dict[str, Any]],
                   db=None, session_id: str = "default") -> Dict[str, Any]:
    """
    Call AI provider with function calling and dual-key failover.
    Returns: {"content": str|None, "tool_calls": list|None}
    """
    available_keys = _get_available_keys()
    
    if available_keys:
        if AI_PROVIDER == "gemini":
            return await _call_gemini_with_failover(available_keys, messages, db, session_id)
        else:
            # Groq not supported with failover yet, fall through
            pass
    
    logger.warning(f"No valid API keys for {AI_PROVIDER}, using fallback intent parser")
    return await _fallback_intent_parser(messages)


async def _call_gemini_with_failover(keys: List[str], messages: List[Dict[str, Any]],
                                       db=None, session_id: str = "default") -> Dict[str, Any]:
    """Call Gemini with automatic failover between keys."""
    from services.agent_tools import execute_tool
    
    model = GEMINI_MODEL
    
    # Convert OpenAI tool format to Gemini format
    gemini_tools = []
    for tool in TOOL_DEFINITIONS:
        func = tool.get("function", {})
        gemini_tools.append({
            "name": func["name"],
            "description": func["description"],
            "parameters": func["parameters"],
        })
    
    # Build initial contents
    contents = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role in ("user", "model"):
            contents.append({"role": role, "parts": [{"text": content}]})
    
    if not contents or contents[-1].get("role") != "user":
        contents.append({"role": "user", "parts": [{"text": messages[-1].get("content", "Hello")}]})
    
    payload = {
        "contents": contents,
        "systemInstruction": {"parts": [{"text": AGENT_SYSTEM_PROMPT}]},
        "tools": [{"functionDeclarations": gemini_tools}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1024},
    }
    
    all_tool_calls = []
    MAX_ITERATIONS = 10
    
    last_error = None
    
    for key_idx, api_key in enumerate(keys):
        logger.info(f"Trying Gemini key #{key_idx + 1} (...{api_key[-6:]})")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            for iteration in range(MAX_ITERATIONS):
                try:
                    url = f"{GEMINI_BASE_URL}/models/{model}:generateContent?key={api_key}"
                    response = await client.post(url, headers={"Content-Type": "application/json"}, json=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                    elif _is_quota_error(response.status_code, response.text):
                        logger.warning(f"Gemini key #{key_idx+1} exhausted, trying next key...")
                        _mark_key_exhausted(api_key)
                        last_error = "quota_exhausted"
                        break  # Try next key
                    else:
                        logger.error(f"Gemini HTTP {response.status_code}")
                        return {"content": "AI service error. Please try again.", "tool_calls": None}
                        
                except httpx.TimeoutException:
                    logger.warning("Gemini timeout")
                    last_error = "timeout"
                    break
                except Exception as e:
                    logger.error(f"Gemini request failed: {type(e).__name__}: {e}")
                    return {"content": "AI service temporarily unavailable. Please try again.", "tool_calls": None}
                
                candidates = data.get("candidates", [])
                if not candidates:
                    return {"content": "I couldn't generate a response. Please try again.", "tool_calls": None}
                
                candidate = candidates[0]
                parts = candidate.get("content", {}).get("parts", [])
                function_calls = [p for p in parts if "functionCall" in p]
                text_parts = [p.get("text", "") for p in parts if "text" in p]
                
                if not function_calls:
                    final_text = "\n".join(text_parts) if text_parts else None
                    return {"content": final_text, "tool_calls": all_tool_calls if all_tool_calls else None}
                
                contents.append({"role": "model", "parts": parts})
                
                tool_parts = []
                for fc in function_calls:
                    fc_data = fc["functionCall"]
                    tool_name = fc_data["name"]
                    tool_args = fc_data.get("args", {})
                    all_tool_calls.append({"name": tool_name, "arguments": tool_args})
                    
                    try:
                        result_str = await execute_tool(tool_name, tool_args, db, session_id)
                        result_data = json.loads(result_str) if result_str.strip().startswith(("{", "[")) else {"output": result_str}
                    except Exception as e:
                        logger.error(f"Tool {tool_name} failed: {e}")
                        result_data = {"error": f"Tool execution failed: {str(e)}"}
                    
                    tool_parts.append({"functionResponse": {"name": tool_name, "response": result_data}})
                
                contents.append({"role": "user", "parts": tool_parts})
                payload["contents"] = contents
            
            # If we broke out of inner loop with quota error, try next key
            if last_error == "quota_exhausted":
                last_error = None
                continue
            break
    
    # All keys failed
    if last_error == "quota_exhausted":
        return {"content": _rule_based_fallback("general"), "tool_calls": all_tool_calls if all_tool_calls else None}
    
    return {
        "content": "AI service is temporarily unavailable. You can still browse the merchant catalog.",
        "tool_calls": all_tool_calls if all_tool_calls else None,
    }


async def _fallback_intent_parser(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Fallback intent parser when no API key is configured."""
    if not messages:
        return {"content": "Hello! How can I help you today?", "tool_calls": None}
    
    last_msg = messages[-1]
    if last_msg.get("role") != "user":
        return {"content": "Here are the results. Would you like to add any items to your cart?", "tool_calls": None}
    
    text = last_msg.get("content", "").lower()
    
    if any(w in text for w in ["search", "find", "show", "looking for", "need", "want"]):
        import re
        max_price = None
        price_match = re.search(r'under\s*₹?\s*(\d+)', text)
        if price_match:
            max_price = float(price_match.group(1))
        return {"content": None, "tool_calls": [{"name": "search_products", "arguments": {"query": text, "max_price": max_price, "in_stock": True}}]}
    
    elif any(w in text for w in ["analytics", "dashboard", "revenue", "profit", "sales"]):
        return {"content": None, "tool_calls": [{"name": "get_merchant_analytics", "arguments": {}}]}
    
    elif any(w in text for w in ["recommend", "suggest", "what should", "growth"]):
        return {"content": None, "tool_calls": [{"name": "get_sales_recommendations", "arguments": {}}]}
    
    elif any(w in text for w in ["add", "cart", "buy"]):
        import re
        position = 1
        m = re.search(r'(\d+)(?:st|nd|rd|th)', text)
        if m:
            position = int(m.group(1))
        return {"content": None, "tool_calls": [{"name": "add_to_cart", "arguments": {"product_position": position, "quantity": 1}}]}
    
    elif any(w in text for w in ["cart", "total", "how much", "bill"]):
        return {"content": None, "tool_calls": [{"name": "get_cart", "arguments": {}}]}
    
    return {"content": "I can help you find products, compare options, and place orders. Try asking 'Find phones under 30000' or 'Show me wireless headphones'.", "tool_calls": None}
