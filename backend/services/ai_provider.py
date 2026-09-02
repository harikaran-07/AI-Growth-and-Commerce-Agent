"""
Commerce Assistant - Rule-based shopping/chat engine.
NO external AI, NO API keys, NO LLM calls.
Uses deterministic intent detection, product search, and template responses.
Supports conversation context for multi-turn interactions.
"""

import os
import re
import json
import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# FAQ Knowledge Base
FAQ_RESPONSES = {
    "payment_methods": {
        "keywords": ["payment", "pay", "upi", "card", "wallet", "razorpay", "netbanking", "method", "option"],
        "response": (
            "We accept the following payment methods:\n\n"
            "💳 **UPI** (Google Pay, PhonePe, Paytm, etc.)\n"
            "🏦 **Net Banking** (All major banks)\n"
            "💰 **Wallets** (Paytm, Mobikwik, Freecharge)\n"
            "💳 **Credit/Debit Cards** (Visa, MasterCard, RuPay)\n\n"
            "All payments are processed securely through Razorpay. 🔒"
        ),
    },
    "shipping": {
        "keywords": ["ship", "delivery", "deliver", "courier", "dispatch", "how long", "how soon", "days"],
        "response": (
            "🚚 **Shipping Information**:\n\n"
            "• Free shipping on orders above ₹499\n"
            "• Standard delivery: 3-5 business days\n"
            "• Express delivery: 1-2 business days (additional charges)\n"
            "• Delivery available across India\n\n"
            "Track your order anytime from the Orders page."
        ),
    },
    "returns": {
        "keywords": ["return", "refund", "exchange", "replace", "cancel"],
        "response": (
            "↩️ **Return & Refund Policy**:\n\n"
            "• 7-day return policy for most items\n"
            "• Items must be unused and in original packaging\n"
            "• Refund processed within 5-7 business days\n"
            "• Electronics: 10-day return window\n\n"
            "To initiate a return, go to Orders → Select Order → Request Return."
        ),
    },
    "contact": {
        "keywords": ["contact", "support", "help", "email", "phone", "call"],
        "response": (
            "📞 **Contact Support**:\n\n"
            "• Email: support@aicommerce.com\n"
            "• Phone: 1800-123-4567 (Toll Free)\n"
            "• Hours: Mon-Sat, 9 AM - 9 PM IST\n\n"
            "You can also use this chat for quick assistance!"
        ),
    },
    "account": {
        "keywords": ["account", "profile", "password", "login", "signup", "register"],
        "response": (
            "👤 **Account Management**:\n\n"
            "• Your session is active and you can shop freely\n"
            "• Cart items are saved in your session\n"
            "• Order history is available in the Orders page\n\n"
            "For account changes, visit Settings."
        ),
    },
}

# Intent patterns - order matters (most specific first)
INTENT_PATTERNS = [
    # Greetings
    {"intent": "greeting", "patterns": [
        r"\b(hello|hi|hey|howdy|greetings|good\s*(morning|afternoon|evening)|sup|yo)\b"
    ]},
    {"intent": "goodbye", "patterns": [
        r"\b(bye|goodbye|see\s*ya|later|exit|quit|close)\b"
    ]},
    # Help
    {"intent": "help", "patterns": [
        r"\b(help|what\s*can\s*you|how\s*do|what\s*do\s*you|capabilities|features)\b"
    ]},

    # Cart actions (check before product search since "add to cart" has "cart")
    {"intent": "show_cart", "patterns": [
        r"\b(show|view|open|see|what('s|\s+is|s)\s+in)\s+(my\s+)?cart\b",
        r"\b(my\s+cart|cart\s+contents|cart\s+total|my\s+order)\b",
        r"\b(how\s+much\s+(is\s+)?(my\s+)?cart|bill|total)\b"
    ]},
    {"intent": "add_to_cart", "patterns": [
        r"\b(add|put|place)\s+(this|it|product|\d+\s*(st|nd|rd|th)?)?\s*(to|in|into)\s+(my\s+)?cart\b",
        r"\b(buy|purchase|get)\s+(this|it)\b",
        r"\b(add)\s+(\d+)\s*(x|pieces?|units?)?\s*(to|in)?\s*(my\s+)?cart\b",
        r"\b(add)\s+(\d+)\b"
    ]},
    {"intent": "remove_from_cart", "patterns": [
        r"\b(remove|delete|drop|take\s*out)\s+(this|it|product|\d+\s*(st|nd|rd|th)?)?\s*(from\s+)?(my\s+)?cart\b"
    ]},
    {"intent": "update_cart_qty", "patterns": [
        r"\b(change|update|set|make)\s+(quantity|qty|amount)\s+(to|of)\s+(\d+)\b",
        r"\b(\d+)\s+(pieces?|units?|qty|quantity)\b"
    ]},
    {"intent": "clear_cart", "patterns": [
        r"\b(clear|empty|reset)\s+(my\s+)?cart\b"
    ]},

    # Order tracking
    {"intent": "order_status", "patterns": [
        r"\b(track|where|status)\s+(my\s+)?(order|package|delivery|shipment)\b",
        r"\b(order|delivery|shipment)\s+(status|track|update)\b",
        r"\b(my\s+order)\b"
    ]},

    # Payment help
    {"intent": "payment_help", "patterns": [
        r"\b(payment|pay|upi|card|wallet|razorpay|netbanking)\s+(method|option|help|how|available)\b",
        r"\b(how\s+(do\s+)?(I|we)\s+pay|payment\s+methods?)\b",
        r"\b(what\s+payment|available\s+payments?)\b"
    ]},

    # Shipping
    {"intent": "shipping_info", "patterns": [
        r"\b(ship|delivery|deliver|courier|dispatch)\s+(info|information|charge|cost|time|days|available|policy)\b",
        r"\b(shipping|delivery)\s+(charge|cost|time|days|estimate)\b",
        r"\b(how\s+(long|soon)\s+(will|does)\s+(it|my\s+order))\b"
    ]},

    # Returns/Refunds
    {"intent": "return_info", "patterns": [
        r"\b(return|refund|exchange|replace)\s+(policy|info|information|item|product)\b",
        r"\b(can\s+I\s+return|how\s+to\s+return)\b"
    ]},

    # Product comparison
    {"intent": "compare", "patterns": [
        r"\b(compare|difference|vs|versus|better|which\s+(one|is))\s+(between|of|the)\b"
    ]},

    # Recommendations
    {"intent": "recommendation", "patterns": [
        r"\b(recommend|suggest|best|top|popular|trending|what\s+(should|do)\s+(I|you)\s+(buy|suggest))\b",
        r"\b(deals|offer|discount|sale|combo|bundle)\b",
        r"\b(gift|present)\b"
    ]},

    # Price queries
    {"intent": "price_query", "patterns": [
        r"\b(price|cost|how\s+much|rate|mrp|expensive|cheap|budget|affordable|under|below|above|over|between)\b.*\b(₹|rs|inr|\d+)\b",
        r"\b(₹|rs\.?)\s*\d+",
        r"\b(under|below|less\s+than)\s+\d+\b",
        r"\b(above|over|more\s+than|greater\s+than)\s+\d+\b"
    ]},

    # Category search
    {"intent": "category_search", "patterns": [
        r"\b(show|find|search|look\s+for|browse|list|display)\s+(me\s+)?(all\s+)?(the\s+)?\b",
        r"\b(electronics|smartphones?|phones?|laptops?|tablets?|headphones?|earphones?|speakers?|cameras?|watches?|tvs?|monitors?|keyboards?|mice|ssds?|routers?|power\s*banks?|webcams?|printers?|projectors?)\b",
        r"\b(grocery|groceries|food|rice|dal|oil|tea|coffee|snacks?|biscuits?|chocolate|noodles?|spices?)\b",
        r"\b(fashion|clothes?|t-?shirts?|shoes?|footwear|sneakers?)\b",
        r"\b(supermarket|detergent|cleaning|household)\b",
        r"\b(smart\s*watches?|fitness\s*trackers?)\b"
    ]},

    # Product search (general)
    {"intent": "product_search", "patterns": [
        r"\b(search|find|show|look\s+for|browse|display|need|want|looking\s+for|get)\b",
        r"\b(wireless|bluetooth|usb|portable|wireless|gaming|pro|max|plus|ultra)\b",
        r"\b(best|top|popular|new|latest|cheap|affordable)\b"
    ]},

    # Stock/availability
    {"intent": "stock_query", "patterns": [
        r"\b(stock|available|availability|in\s*stock|out\s+of\s+stock|sold\s*out|deliverable)\b"
    ]},

    # Product details
    {"intent": "product_details", "patterns": [
        r"\b(tell\s+me\s+about|details?|specs?|specifications?|features?|description|info(?:rmation)?)\s+(of|about|for|on)\b",
        r"\b(detail|specs?|features?)\s*(of|about|for)?\s*(this|that|the)\s*(product|item)?\b"
    ]},

    # Thank you
    {"intent": "thank_you", "patterns": [
        r"\b(thanks?|thank\s*you|thx|ty|appreciate)\b"
    ]},
]

# Category aliases for flexible matching
CATEGORY_ALIASES = {
    "phone": "Smartphones",
    "phones": "Smartphones",
    "mobile": "Smartphones",
    "mobiles": "Smartphones",
    "smartphone": "Smartphones",
    "laptop": "Laptops",
    "laptops": "Laptops",
    "notebook": "Laptops",
    "tablet": "Tablets",
    "tablets": "Tablets",
    "ipad": "Tablets",
    "headphone": "Headphones",
    "headphones": "Headphones",
    "earphone": "Earphones",
    "earphones": "Earphones",
    "earbuds": "Earphones",
    "tws": "Earphones",
    "speaker": "Speakers",
    "speakers": "Speakers",
    "soundbar": "Speakers",
    "camera": "Cameras",
    "cameras": "Cameras",
    "watch": "Smart Watches",
    "watches": "Smart Watches",
    "smartwatch": "Smart Watches",
    "tv": "TVs",
    "television": "TVs",
    "televisions": "TVs",
    "tvs": "TVs",
    "monitor": "Monitors",
    "monitors": "Monitors",
    "display": "Monitors",
    "keyboard": "Keyboards",
    "keyboards": "Keyboards",
    "mouse": "Mice",
    "mice": "Mice",
    "ssd": "SSDs",
    "ssds": "SSDs",
    "storage": "SSDs",
    "drive": "SSDs",
    "router": "Routers",
    "routers": "Routers",
    "wifi": "Routers",
    "powerbank": "Power Banks",
    "power bank": "Power Banks",
    "power banks": "Power Banks",
    "webcam": "Webcams",
    "webcams": "Webcams",
    "printer": "Printers",
    "printers": "Printers",
    "projector": "Projectors",
    "projectors": "Projectors",
    "grocery": "Grocery",
    "groceries": "Grocery",
    "food": "Grocery",
    "rice": "Grocery",
    "dal": "Grocery",
    "oil": "Grocery",
    "tea": "Grocery",
    "coffee": "Grocery",
    "snack": "Grocery",
    "snacks": "Grocery",
    "biscuit": "Grocery",
    "biscuits": "Grocery",
    "chocolate": "Grocery",
    "noodle": "Grocery",
    "noodles": "Grocery",
    "spice": "Grocery",
    "spices": "Grocery",
    "flour": "Grocery",
    "atta": "Grocery",
    "fashion": "Fashion",
    "clothes": "Fashion",
    "clothing": "Fashion",
    "tshirt": "Fashion",
    "t-shirt": "Fashion",
    "shoe": "Fashion",
    "shoes": "Fashion",
    "sneaker": "Fashion",
    "sneakers": "Fashion",
    "footwear": "Fashion",
    "supermarket": "Supermarket",
    "detergent": "Supermarket",
    "cleaning": "Supermarket",
    "household": "Supermarket",
    "accessories": "Accessories",
    "accessory": "Accessories",
    "cable": "Accessories",
    "cables": "Accessories",
    "charger": "Accessories",
    "case": "Accessories",
    "cover": "Accessories",
    "protector": "Accessories",
    "hub": "Accessories",
    "adapter": "Accessories",
}

# Quick action buttons for the chatbot
QUICK_ACTIONS = [
    {"label": "Find Products", "message": "Show me popular products"},
    {"label": "Today's Deals", "message": "Show me deals and discounts"},
    {"label": "Show Cart", "message": "Show my cart"},
    {"label": "Track Order", "message": "Track my order"},
    {"label": "Help", "message": "Help"},
]


def detect_intent(text: str) -> Dict[str, Any]:
    """
    Detect user intent from text using pattern matching.
    Returns: {"intent": str, "entities": dict}
    """
    text_lower = text.lower().strip()
    entities = {}

    # Extract price entities - with or without currency symbol
    price_match = re.search(r'(?:under|below|less\s+than|below)\s*(?:₹|rs\.?\s*)?(\d[\d,]*)', text_lower)
    if price_match:
        entities["max_price"] = float(price_match.group(1).replace(",", ""))

    price_match_high = re.search(r'(?:above|over|more\s+than|greater\s+than)\s*(?:₹|rs\.?\s*)?(\d[\d,]*)', text_lower)
    if price_match_high:
        entities["min_price"] = float(price_match_high.group(1).replace(",", ""))

    # Extract ₹ price (with currency symbol)
    rupee_match = re.search(r'(?:₹|rs\.?\s*)(\d[\d,]*)', text_lower)
    if rupee_match and "max_price" not in entities and "min_price" not in entities:
        entities["max_price"] = float(rupee_match.group(1).replace(",", ""))

    # Extract quantity
    qty_match = re.search(r'\b(\d+)\s*(?:pieces?|units?|qty|quantity|x)\b', text_lower)
    if qty_match:
        entities["quantity"] = int(qty_match.group(1))

    # Extract position (1st, 2nd, etc.)
    pos_match = re.search(r'\b(\d+)(?:st|nd|rd|th)\b', text_lower)
    if pos_match:
        entities["position"] = int(pos_match.group(1))

    # Extract category
    for alias, category in CATEGORY_ALIASES.items():
        if re.search(r'\b' + re.escape(alias) + r'\b', text_lower):
            entities["category"] = category
            break

    # Extract search keywords (remove common filler words)
    stop_words = {
        "show", "me", "find", "search", "for", "the", "a", "an", "in", "under",
        "below", "above", "over", "and", "or", "with", "best", "top", "popular",
        "please", "can", "you", "i", "want", "need", "looking", "get", "buy",
        "display", "list", "browse", "some", "any", "all", "of", "that", "this",
        "its", "it", "my", "your", "our", "is", "are", "was", "were", "have",
        "has", "had", "do", "does", "did", "will", "would", "could", "should",
        "may", "might", "shall", "to", "from", "on", "at", "by", "for", "about",
        "rs", "rs.", "inr", "₹", "price", "cost", "how", "much",
    }
    words = re.findall(r'\b[a-z]+\b', text_lower)
    search_words = [w for w in words if w not in stop_words and len(w) > 1]
    if search_words:
        entities["query"] = " ".join(search_words)

    # Match intent (most specific first)
    for intent_def in INTENT_PATTERNS:
        for pattern in intent_def["patterns"]:
            if re.search(pattern, text_lower):
                return {"intent": intent_def["intent"], "entities": entities}

    # Fallback: if it looks like a product search
    if entities.get("query") or entities.get("category") or entities.get("max_price"):
        return {"intent": "product_search", "entities": entities}

    return {"intent": "unknown", "entities": entities}


async def generate_response(intent_result: Dict, tools_fn, db=None, session_id: str = "default") -> Dict[str, Any]:
    """
    Generate a response based on detected intent.
    Uses deterministic logic - no AI model involved.
    Maintains conversation context via session_id.
    """
    intent = intent_result["intent"]
    entities = intent_result["entities"]

    if intent == "greeting":
        return {
            "content": "Hello! 👋 Welcome to Commerce Assistant. I can help you find products, check prices, manage your cart, and more. What are you looking for?",
            "tool_calls": None,
            "quick_actions": QUICK_ACTIONS,
        }

    if intent == "goodbye":
        return {
            "content": "Thank you for visiting! Have a great day! 😊 Feel free to come back anytime.",
            "tool_calls": None,
        }

    if intent == "thank_you":
        return {
            "content": "You're welcome! 😊 Is there anything else I can help you with?",
            "tool_calls": None,
            "quick_actions": QUICK_ACTIONS,
        }

    if intent == "help":
        return {
            "content": (
                "Here's what I can help you with:\n\n"
                "🔍 **Product Search**: \"Show me laptops\" or \"Find headphones under 3000\"\n"
                "🛒 **Cart**: \"Add this to cart\" or \"Show my cart\"\n"
                "📦 **Orders**: \"Track my order\"\n"
                "💳 **Payments**: \"What payment methods are available?\"\n"
                "🚚 **Shipping**: \"Shipping information\"\n"
                "↩️ **Returns**: \"Return policy\"\n"
                "💡 **Recommendations**: \"Suggest something under 5000\"\n\n"
                "Just type naturally and I'll help you!"
            ),
            "tool_calls": None,
            "quick_actions": QUICK_ACTIONS,
        }

    if intent == "show_cart":
        return {
            "content": None,
            "tool_calls": [{"name": "get_cart", "arguments": {}}],
        }

    if intent == "add_to_cart":
        product_id = entities.get("product_id")
        product_position = entities.get("position")
        quantity = entities.get("quantity", 1)
        return {
            "content": None,
            "tool_calls": [{"name": "add_to_cart", "arguments": {
                "product_id": product_id,
                "product_position": product_position,
                "quantity": quantity,
            }}],
        }

    if intent == "remove_from_cart":
        return {
            "content": "To remove an item from your cart, please visit the Cart page or let me know which product you'd like to remove.",
            "tool_calls": None,
            "quick_actions": [
                {"label": "Show Cart", "message": "Show my cart"},
                {"label": "Continue Shopping", "message": "Show me popular products"},
            ],
        }

    if intent == "clear_cart":
        return {
            "content": "To clear your cart, please visit the Cart page and remove items individually, or I can help you start fresh.",
            "tool_calls": None,
            "quick_actions": [
                {"label": "Show Cart", "message": "Show my cart"},
            ],
        }

    if intent == "order_status":
        return {
            "content": "You can track your order on the Orders page. If you have an order ID, I can look up the status for you. Would you like to check a specific order?",
            "tool_calls": None,
            "quick_actions": [
                {"label": "View Orders", "message": "Show my orders"},
            ],
        }

    if intent == "payment_help":
        return {
            "content": FAQ_RESPONSES["payment_methods"]["response"],
            "tool_calls": None,
        }

    if intent == "shipping_info":
        return {
            "content": FAQ_RESPONSES["shipping"]["response"],
            "tool_calls": None,
        }

    if intent == "return_info":
        return {
            "content": FAQ_RESPONSES["returns"]["response"],
            "tool_calls": None,
        }

    if intent == "compare":
        return {
            "content": "I can help you compare products! Please tell me which products you'd like to compare, or search for a category first and I'll show you options side by side.",
            "tool_calls": None,
            "quick_actions": [
                {"label": "Find Products", "message": "Show me popular products"},
            ],
        }

    if intent == "recommendation":
        # If they specify a category/price, search for those
        if entities.get("category") or entities.get("max_price") or entities.get("query"):
            return {
                "content": None,
                "tool_calls": [{"name": "search_products", "arguments": {
                    "query": entities.get("query", ""),
                    "category": entities.get("category"),
                    "max_price": entities.get("max_price"),
                    "min_price": entities.get("min_price"),
                    "in_stock": True,
                }}],
            }
        return {
            "content": None,
            "tool_calls": [{"name": "search_products", "arguments": {
                "query": "popular trending",
                "in_stock": True,
            }}],
        }

    if intent == "product_search":
        query_parts = []
        if entities.get("query"):
            query_parts.append(entities["query"])
        if entities.get("category"):
            query_parts.append(entities["category"])

        return {
            "content": None,
            "tool_calls": [{"name": "search_products", "arguments": {
                "query": " ".join(query_parts) if query_parts else "",
                "category": entities.get("category"),
                "max_price": entities.get("max_price"),
                "min_price": entities.get("min_price"),
                "in_stock": True,
            }}],
        }

    if intent == "category_search":
        return {
            "content": None,
            "tool_calls": [{"name": "search_products", "arguments": {
                "query": entities.get("query", ""),
                "category": entities.get("category"),
                "max_price": entities.get("max_price"),
                "min_price": entities.get("min_price"),
                "in_stock": True,
            }}],
        }

    if intent == "price_query":
        return {
            "content": None,
            "tool_calls": [{"name": "search_products", "arguments": {
                "query": entities.get("query", ""),
                "category": entities.get("category"),
                "max_price": entities.get("max_price"),
                "min_price": entities.get("min_price"),
                "in_stock": True,
            }}],
        }

    if intent == "stock_query":
        return {
            "content": "All products shown are currently in stock. If you're looking for a specific product, let me know and I'll check its availability.",
            "tool_calls": None,
        }

    if intent == "product_details":
        return {
            "content": "Tell me which product you'd like to know more about, and I'll get the details for you!",
            "tool_calls": None,
            "quick_actions": [
                {"label": "Find Products", "message": "Show me popular products"},
            ],
        }

    # Unknown intent - try product search as fallback
    if entities.get("query") or entities.get("category"):
        return {
            "content": None,
            "tool_calls": [{"name": "search_products", "arguments": {
                "query": entities.get("query", ""),
                "category": entities.get("category"),
                "max_price": entities.get("max_price"),
                "min_price": entities.get("min_price"),
                "in_stock": True,
            }}],
        }

    return {
        "content": (
            "I can help you with products, prices, availability, your cart, orders, and checkout.\n\n"
            "Try asking something like \"Show me headphones under 3000\" or \"What payment methods do you accept?\""
        ),
        "tool_calls": None,
        "quick_actions": [
            {"label": "Find Products", "message": "Show me popular products"},
            {"label": "Show Cart", "message": "Show my cart"},
            {"label": "Track Order", "message": "Track my order"},
            {"label": "Help", "message": "Help"},
        ],
    }


def get_tool_definitions() -> List[Dict[str, Any]]:
    """Return tool definitions (kept for backward compatibility)."""
    return [
        {"name": "search_products", "description": "Search products"},
        {"name": "get_cart", "description": "Get cart contents"},
        {"name": "add_to_cart", "description": "Add product to cart"},
    ]


async def call_llm(messages: List[Dict[str, Any]], tools: List[Dict[str, Any]],
                   db=None, session_id: str = "default") -> Dict[str, Any]:
    """
    Main entry point - processes messages using rule-based intent detection.
    No external AI API is called.
    Executes tool calls and returns results.
    """
    if not messages:
        return {"content": "Hello! How can I help you today?", "tool_calls": None, "quick_actions": QUICK_ACTIONS}

    # Get the last user message
    last_msg = None
    for msg in reversed(messages):
        if msg.get("role") == "user":
            last_msg = msg
            break

    if not last_msg:
        return {"content": "How can I help you?", "tool_calls": None, "quick_actions": QUICK_ACTIONS}

    text = last_msg.get("content", "")
    if not text.strip():
        return {"content": "Please type a message and I'll help you!", "tool_calls": None, "quick_actions": QUICK_ACTIONS}

    # Detect intent
    intent_result = detect_intent(text)
    logger.info(f"Intent detected: {intent_result['intent']} | Entities: {intent_result['entities']}")

    # Generate response
    response = await generate_response(intent_result, None, db=db, session_id=session_id)

    # Tool execution happens in agent.py chat endpoint (not here)
    return response


# Backward compatibility aliases
generate_ai_response = None  # Not used anymore
