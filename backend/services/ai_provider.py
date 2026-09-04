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

# ────────────────────────────────────────────────────────────
# General knowledge bank — the assistant can hold a normal
# conversation about concepts, the store, and payments without
# ever inventing product data or calling an external AI.
# ────────────────────────────────────────────────────────────
GENERAL_KB = [
    {
        "id": "store_overview",
        "keywords": ["how does this store work", "how does this website work", "how does the store work",
                      "what is this store", "what is this website", "what is this app", "about this store",
                      "how does the app work", "what is aicomm", "about the project", "tell me about the store"],
        "response": (
            "**AI Growth & Commerce Agent** is a demo marketplace with an AI assistant called the *Commerce Assistant*. "
            "Here's how it works:\n\n"
            "🛍️ **Store** — browse a real catalog of thousands of products (smartphones, laptops, audio, fashion and more).\n"
            "🤖 **Commerce Assistant** — talk to it in plain language to find products, compare options, manage your cart and check out.\n"
            "💳 **Payments** — checkout runs through **Razorpay in TEST MODE**, so no real money moves.\n"
            "📈 **Growth Agent** — the dashboard analyzes synthetic demo data to propose safe, approval-gated growth actions.\n\n"
            "Just tell me what you're looking for and I'll take it from there!"
        ),
    },
    {
        "id": "razorpay",
        "keywords": ["what is razorpay", "razorpay is", "what does razorpay", "razorpay company", "who is razorpay"],
        "response": (
            "Razorpay is a popular Indian **payment gateway** — a service that lets online stores safely accept payments "
            "via UPI, cards, net banking and wallets. Merchants create a *payment order*, customers pay on Razorpay's "
            "secure page, and Razorpay verifies the transaction back to the merchant.\n\n"
            "This demo store uses **Razorpay TEST MODE**: checkout flows are fully real (order created → pay → signature "
            "verified) but no actual money is charged."
        ),
    },
    {
        "id": "payment_gateway",
        "keywords": ["what is a payment gateway", "what are payment gateways", "what is payment gateway", "define payment gateway"],
        "response": (
            "A **payment gateway** is the secure bridge between a store and the banks/networks that move money. "
            "When you pay, the gateway encrypts your details, asks your bank to approve the charge, and tells the store "
            "whether payment succeeded — all in a few seconds. Popular examples in India include Razorpay, PayU and CCAvenue."
        ),
    },
    {
        "id": "upi",
        "keywords": ["what is upi", "what is a upi", "upi means", "upi stands for", "what does upi mean"],
        "response": (
            "**UPI (Unified Payments Interface)** is India's instant bank-to-bank payment system. You link a bank account "
            "to a UPI ID (like name@bank) and pay directly from your phone with apps such as Google Pay, PhonePe or Paytm — "
            "no card numbers or account details are shared with the store. This store accepts UPI through Razorpay."
        ),
    },
    {
        "id": "payment_verification",
        "keywords": ["how does payment verification work", "signature verification", "how is payment verified",
                      "verify payment", "payment verification"],
        "response": (
            "Payment verification protects both sides. After you pay, Razorpay sends the store a **signature** made from the "
            "payment details + the merchant's secret key. The backend re-computes that signature and only marks the order "
            "**paid** when it matches. If the signature is invalid the payment is treated as failed — an audit event is "
            "recorded and you can retry safely. The secret key never leaves the server."
        ),
    },
    {
        "id": "test_mode",
        "keywords": ["test mode", "is this real payment", "real money", "demo payment", "test payment",
                      "will i be charged", "do i pay real money", "fake payment"],
        "response": (
            "This store runs **Razorpay TEST MODE** — checkout is fully functional but **no real money is charged**. "
            "Use Razorpay's test cards/UPI when the payment window opens. Real orders, order history and the audit trail "
            "all still work normally with test payments."
        ),
    },
    {
        "id": "refund",
        "keywords": ["how do refunds work", "refund time", "when will i get refunded", "how long refund"],
        "response": (
            "Refunds follow the return policy: most items can be returned within 7 days (10 days for electronics). "
            "Once a return is approved, the refund is processed in 5–7 business days back to the original payment method. "
            "Refunds on Razorpay TEST MODE payments are simulated for the demo."
        ),
    },
    {
        "id": "checkout_meaning",
        "keywords": ["what does checkout mean", "what is checkout", "meaning of checkout", "checkout means"],
        "response": (
            "**Checkout** is the final step of shopping: the store locks in your cart, calculates the total from "
            "trusted server-side prices (subtotal + tax + shipping), creates an order, and sends you to payment. "
            "In this app, checkout creates a real Razorpay TEST MODE order that you then pay — the order is only "
            "confirmed after payment is verified."
        ),
    },
    {
        "id": "product_vs_order",
        "keywords": ["difference between a product and an order", "product vs order", "what is the difference between product and order"],
        "response": (
            "A **product** is an item in the catalog (with a price, stock and image). An **order** is a purchase record "
            "created at checkout — it locks in the products, quantities and prices for that specific purchase, tracks "
            "payment status, and becomes part of your order history. One order can contain several products."
        ),
    },
    {
        "id": "ai_agent",
        "keywords": ["what is an ai agent", "what is ai agent", "what are ai agents", "define ai agent", "ai agent meaning"],
        "response": (
            "An **AI agent** is a program that can take *actions* toward a goal — not just answer questions. "
            "A shopping agent can search a catalog, add items to a cart and start checkout. "
            "This project adds safety rails: agents can only act through **approved tools**, every money action is "
            "**bounded by policy** and **gated behind approval**, and everything is written to an **audit trail**."
        ),
    },
    {
        "id": "machine_learning",
        "keywords": ["what is machine learning", "what is ml", "explain machine learning", "define machine learning", "ml is"],
        "response": (
            "**Machine learning** is a branch of AI where a computer learns patterns from data instead of following "
            "hand-written rules for every case. Example: show it thousands of labeled product photos and it learns to "
            "recognize a smartphone. This assistant uses *deterministic* rules over the real catalog (no external ML API), "
            "so its answers are always traceable to actual data."
        ),
    },
    {
        "id": "ai_basics",
        "keywords": ["what is ai", "what is artificial intelligence", "explain ai", "ai in simple", "what is an ai"],
        "response": (
            "**AI (artificial intelligence)** is technology that lets computers do things that normally need human "
            "intelligence — understanding language, recognizing images, making recommendations. This demo pairs two "
            "AI ideas with real commerce: an **AI buyer** that discovers and purchases products, and a **growth agent** "
            "that finds revenue opportunities for the merchant — both kept safe by policy checks and approvals."
        ),
    },
    {
        "id": "what_is_llm",
        "keywords": ["what is an llm", "what is llm", "llm meaning", "what is a language model", "explain llm"],
        "response": (
            "An **LLM (large language model)** is an AI trained on huge amounts of text to predict and generate language. "
            "This demo intentionally runs without an external LLM — the Commerce Assistant uses deterministic, "
            "explainable logic over the real catalog so no API key is required and every answer is auditable."
        ),
    },
    {
        "id": "python",
        "keywords": ["what is python", "python language", "python programming"],
        "response": "Python is a general-purpose programming language popular for web apps, automation, data analysis and AI. (This store's backend is built with Python + FastAPI!)",
    },
]


def answer_general_question(text: str) -> Optional[str]:
    """Return a knowledge-bank answer for a general/concept question, or None."""
    tl = " ".join(text.lower().split())
    for topic in GENERAL_KB:
        for kw in topic["keywords"]:
            if kw in tl:
                return topic["response"]
    return None


WORD_NUMBERS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}

# Words that signal a NEW product search when they appear alone in a short
# follow-up (as opposed to continuation attributes like "wireless").
SEARCH_TRIGGERS = {"show", "find", "search", "need", "want", "looking", "get", "browse", "display", "list", "recommend", "suggest"}


def resolve_followup_text(text: str, session_data: Dict) -> str:
    """
    Rewrite short follow-up messages so the intent engine can act on them
    using the previous turn's context (last search / last added product).
    Non-follow-ups are returned unchanged.
    """
    t = text.strip().lower()
    if not t:
        return text

    last_query = session_data.get("last_search_query") or {}
    has_search = bool(session_data.get("last_search_results"))
    prev_q = (last_query.get("query") or "").strip()
    prev_cat = (last_query.get("category") or "").strip()
    prev_text = prev_q or prev_cat or "products"

    # 1. "which is better / cheaper / the best one / which should I pick"
    if has_search and (re.search(r"\b(which|what)\s+(one\s+)?(is|are|would\s+be|s)\s+(the\s+)?(better|best|cheaper|cheapest|faster|more\s+worth|worth)\b", t) or \
       re.search(r"\bwhich\s+(one\s+)?(should\s+i|do\s+you\s+(recommend|suggest)|is\s+better)\b", t) or \
       re.search(r"\b(compare|comparison)\b.*\b(them|these|those|the\s+(first|second|two|ones|three)|this|that)\b", t) or \
                       re.search(r"\b(which)\s+(of|among)\s+(them|these|those)\b", t)):
        return "compare them for me"

    # 2. Set quantity: "make it two", "set to 3", "make that 5"
    m = re.search(
        r"\b(make|set|change|update|increase|reduce)\s+(it|this|that|the\s+(qty|quantity)|qty|quantity|amount|to)\s*(to|as|=)?\s*"
        r"(one|two|three|four|five|six|seven|eight|nine|ten|\d+)\b", t
    )
    if m and re.search(r"\b(make|set|change|update|increase|reduce)\b", t):
        q = m.group(5)
        num = int(q) if q.isdigit() else WORD_NUMBERS.get(q, 1)
        return f"update quantity to {num}"

    # 3. Budget-only follow-up: "under ₹3,000" / "below 5000" after a search
    budget_only = re.search(
        r"^\s*(?:under|below|within|upto|up\s+to|at\s+most|less\s+than|max|around|about)?\s*(?:₹|rs\.?\s*)?([\d,]+)\s*$", t
    )
    if budget_only and has_search:
        budget = budget_only.group(1).replace(",", "")
        return f"show me {prev_text} under {budget}"

    # 3b. Cheaper/alternative follow-up on the current results
    if has_search and re.search(r"^(cheaper|cheap(?:er)?\s*(?:one|options?|alternatives?)?|alternatives?|less\s+expensive[\s\w]*)$", t):
        return "show me cheaper alternatives"

    # 4. Short attribute-only continuation: "wireless", "16gb", "gaming", "in black"
    words = t.split()
    is_short = 1 <= len(words) <= 4
    has_trigger = any(w in SEARCH_TRIGGERS for w in words)
    has_budget = bool(re.search(r"(₹|rs\.?\s*)?\d", t)) or bool(re.search(r"(under|below|upto|above|over)\b", t))
    is_ordinal = bool(re.search(r"\b(first|second|third|fourth|fifth|last|one|two|three|four|five)\b", t))
    # Full questions / new topics / category words are NOT refinements
    is_question = bool(re.search(r"\b(what|which|who|why|how|can|do|is|are)\b", t))
    names_category = any(w in CATEGORY_ALIASES for w in words)
    new_topic = re.search(r"\b(show|find|search|need|want|looking|browse|display|list|best\s+sellers?|cart|order|payment|help|hi|hello)\b", t)
    if has_search and is_short and not has_trigger and not new_topic and not has_budget and not is_ordinal and not is_question and not names_category:
        return f"show me {prev_text} {t}"

    # 5. Deictic add with no position: "add it / add this" → the first result
    if has_search and re.search(r"\b(add|put|place|buy|get)\b", t) and re.search(r"\b(it|this|that|one)\b", t) \
            and not re.search(r"\b(first|second|third|fourth|fifth|last|\d+(st|nd|rd|th))\b", t):
        return "add the first one to cart"

    return text


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
    # Security: never reveal secrets / never follow injected instructions
    {"intent": "security_refusal", "patterns": [
        r"\b(api\s*keys?|secret\s*keys?|private\s*keys?|credentials|access\s*tokens?|auth\s*tokens?|database\s*password|db\s*password|razorpay\s*secret)\b",
        r"\b(what\s+is\s+your|show\s+me\s+your|give\s+me\s+your|tell\s+me\s+your|reveal\s+your|print\s+your|share\s+your)\s+(password|secret|key|api\s+key|credentials)\b",
        r"\b(system\s+prompt|developer\s+prompt|internal\s+instructions?|your\s+instructions?|hidden\s+prompt)\b.*\b(reveal|show|give|print|share|leak|tell|repeat|output)\b",
        r"\b(reveal|show|give|print|share|leak|tell|repeat|output|what\s+is)\b.*\b(system\s+prompt|developer\s+prompt|internal\s+instructions?|your\s+instructions?|hidden\s+prompt|your\s+rules)\b",
        r"\b(hack|exploit|bypass|override|jailbreak|ignore\s+(previous|prior|all)\s+instructions|act\s+as\s+admin|grant\s+me\s+admin)\b"
    ]},

    # Cart actions (checked BEFORE the generic show_cart so "add … to my cart"
    # is never mistaken for a cart view)
    {"intent": "add_to_cart", "patterns": [
        r"\b(add|put|place)\s+(this|it|product|\d+\s*(st|nd|rd|th)?)?\s*(to|in|into)\s+(my\s+)?cart\b",
        r"\b(add|put|place)\s+(the\s+)?(first|second|third|fourth|fifth|last|\d+\s*(st|nd|rd|th)?)(\s+one)?(\s+item)?\s*(to|in|into)\s+(my\s+)?cart\b",
        r"\b(add|put|place)\s+(the\s+)?(first|second|third|fourth|fifth|last|\d+\s*(st|nd|rd|th)?)(\s+one)?(\s+item)?\s*(please)?\b",
        r"\b(buy|purchase|get)\s+(this|it|the\s+first\s+one)\b",
        r"\b(add)\s+(\d+)\s*(x|pieces?|units?)?\s*(to|in)?\s*(my\s+)?cart\b",
        r"\b(add)\s+(\d+)\b",
        # "add two of them / of those / of these" → default position 1
        r"\b(add|put|place)\s+(the\s+)?(one|two|three|four|five|six|seven|eight|nine|ten)\s+(of|more\s+of)\s+(them|those|these)\b",
        r"\b(add|put|place)\s+(a\s+)?(one|two|three|four|five|six|seven|eight|nine|ten)\s+(more\s+)?(of\s+)?(them|those|these)?\s*(to|in|into)?\s*(my\s+)?cart\b",
    ]},
    {"intent": "show_cart", "patterns": [
        r"\b(show|view|open|see|what('s|\s+is|s)\s+in)\s+(my\s+)?cart\b",
        r"\b(what('s|\s+is)\s+(my\s+)?cart\s+total|cart\s+total)\b",
        r"^\s*(my\s+cart|cart\s+contents)(\s+please)?\s*[!.?]*\s*$",
        r"\b(how\s+much\s+(is\s+)?(my\s+)?cart|bill|total)\b",
        r"\b(what('s|\s+is)\s+(my\s+)?total)\b",
        r"\b(how\s+many\s+(items?|products?)|cart\s+count)\s+(do\s+i\s+have|is\s+in\s+my\s+cart)\b"
    ]},
    {"intent": "checkout", "patterns": [
        r"\b(checkout|check\s*out)\b",
        r"\b(place|complete|finish)\s+(my\s+|the\s+)?order\b",
        r"\b(proceed\s+to\s+(payment|checkout)|pay\s+now|buy\s+now|complete\s+(the\s+)?purchase)\b",
        r"\b(i\s+am\s+ready\s+to\s+pay|let'?s\s+pay|pay\s+for\s+(my\s+)?(cart|order))\b"
    ]},
    {"intent": "remove_from_cart", "patterns": [
        r"\b(remove|delete|drop|take\s*out)\s+(the\s+)?(last|first|second|third|fourth|fifth|\d+\s*(st|nd|rd|th))\s*(item|one|product)?\s*((from\s+)?(my\s+)?cart)?\s*[!.?]*\s*$",
        r"\b(remove|delete|drop|clear\s+out)\s+(this|that|it|the\s+(item|product)|an?\s+item)\s*(from\s+)?(my\s+)?cart\b",
        r"\b(remove|delete|drop)\s+(\d+)\s*(items?|products?)\s*((from\s+)?(my\s+)?cart)?\s*[!.?]*\s*$",
        r"\b(remove|delete|drop|take\s+off)\s+([a-z][a-z0-9 -]{1,40}?)\s*((from|out\s+of)\s+(my\s+)?cart)?\s*[!.?]*\s*$"
    ]},
    {"intent": "update_cart_qty", "patterns": [
        r"\b(change|update|set|make|reduce|increase)\s+(quantity|qty|amount|count|it)\s+(to|of|as|=)\s*(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\b",
        r"\b(change|update|set|make)\s+(the\s+)?(quantity|qty|amount)\s+(to|of)\s+(\d+)\b",
        r"\b(\d+)\s*(pieces?|units?|qty|quantity)\b"
    ]},
    {"intent": "clear_cart", "patterns": [
        r"\b(clear|empty|reset)\s+(my\s+)?cart\b"
    ]},

    # Accessories / compatible items for a product (cross-sell)
    {"intent": "accessories", "patterns": [
        r"\b(what\s+)?(accessor(?:ies|y)|compatible\s+items|add-?ons|companion)\s+(go(?:es|ing)?|for|with|to|that\s+go)\b",
        r"\b(accessor(?:ies|y)|extras|add-?ons|bundle|combo)\s+(for|with|to|that\s+go\s+with)\s+(this|that|it|the\s+product|\d+\s*(st|nd|rd|th)?)\b",
        r"\b(recommend|suggest|show|find)\s+(me\s+)?(some\s+)?accessor(?:ies|y)s?\b",
        r"\b(what|which)\s+(accessor|add-?ons|extras)\b"
    ]},

    # Cheaper / budget alternatives to the currently viewed product
    {"intent": "cheaper_alternative", "patterns": [
        r"\b(cheaper|cheapest|less\s+expensive|more\s+affordable|budget\s+alternative|cheap\s+alternative)s?\b",
        r"\b(alternative|alternatives|option|options|similar)\s+(that\s+are\s+)?(cheaper|less\s+expensive|under|below)\b",
        r"\b(show|find|see)\s+(me\s+)?(a\s+)?(cheaper|cheapest|cheap)\s+(one|option|alternative|version)?s?\b",
        r"\b(lower\s+(priced|price)|price\s+under|under\s+this\s+price)\b"
    ]},

    # Order tracking
    {"intent": "order_status", "patterns": [
        r"\b(track|where|status)\s+(my\s+)?(order|package|delivery|shipment)\b",
        r"\b(order|delivery|shipment)\s+(status|track|update)\b",
        r"\b(my\s+order)\b"
    ]},

    # Payment failure / troubleshooting
    {"intent": "payment_failed", "patterns": [
        r"\b(payment|pay|transaction|order)\s+(failed|was\s*not\s*completed|didn't\s*go\s*through|didn't\s*work|was\s*declined|declined|errored|error|unsuccessful|not\s*successful)\b",
        r"\b(my\s+)?(payment|pay)\s+(didn't|did\s+not)\s*(go|work|complete|succeed)\b",
        r"\b(payment|pay)\s+failure\b"
    ]},

    # Payment help
    {"intent": "payment_help", "patterns": [
        r"\b(payment|pay|upi|card|wallet|razorpay|netbanking)\s+(method|option|help|how|available)\b",
        r"\b(how\s+(do\s+)?(I|we)\s+pay|payment\s+methods?)\b",
        r"\b(what\s+payment|available\s+payments?)\b",
        r"\b(how\s+can\s+i\s+pay|ways\s+to\s+pay)\b"
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
        r"\b(compare|difference|vs|versus|better|which\s+(one|is))\s+(between|of|the)\b",
        r"\b(compare|comparison)\s+(them|these|those|it|this|that|the\s+(first|second|third|two|three|ones|products?))\b",
        r"\bwhich\s+(one\s+)?(is|would\s+be|s)\s+(the\s+)?(better|best|cheaper|cheapest|worth|more\s+expensive)\b",
        r"\bwhich\s+(should|do|would)\s+(i|you)\s+(pick|choose|buy|go\s+with|recommend)\b",
        r"\b(better|best)\s+(option|choice|deal|value)\b",
        r"\bwhich\s+(of|among)\s+(them|these|those)\b"
    ]},

    # Best Sellers
    {"intent": "best_sellers", "patterns": [
        r"\b(best\s*sellers?|bestselling|best\s*selling|top\s*selling|most\s*sold|trending\s*now|what('s|\s+is)\s+popular)\b",
        r"\b(show|find|get|give|display|list)\s+(me\s+)?(the\s+)?(best\s*sellers?|top\s*products?)\b",
        r"\b(best\s*products?|popular\s*products?)\b"
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
        r"\b(electronics|smartphones?|phones?|laptops?|tablets?|headphones?|earphones?|speakers?|cameras?|watches?|tvs?|television|monitors?|keyboards?|mice|ssds?|routers?|power\s*banks?|webcams?|printers?|projectors?)\b",
        r"\b(fashion|clothes?|t-?shirts?|shoes?|footwear|sneakers?)\b",
        r"\b(smart\s*watches?|fitness\s*trackers?)\b",
        r"\b(best\s*sellers?|bestselling|trending|popular)\b"
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
        r"\b(detail|specs?|features?)\s*(of|about|for)?\s*(this|that|the)\s*(product|item)?\b",
        r"\b(tell\s+me\s+about|more\s+about)\s+(this|that|it|the\s+(first|second|third|fourth|fifth|last)|\d+\s*(st|nd|rd|th))\b"
    ]},

    # Who / what the assistant is
    {"intent": "identity", "patterns": [
        r"\b(who|what)\s+(are\s+you|is\s+your\s+name|do\s+you\s+do|kind\s+of\s+(assistant|bot))\b",
        r"\b(tell\s+me\s+about\s+yourself|about\s+you\s*\?|are\s+you\s+(real|human|a\s+bot|ai|an\s+ai))\b"
    ]},

    # General knowledge / concept questions (catch-all AFTER commerce patterns)
    {"intent": "general_chat", "patterns": [
        r"\b(what\s+is|what\s+are|what's|explain|define|meaning\s+of)\b",
        r"\b(how\s+does|how\s+do\s+i|how\s+can\s+i|tell\s+me\s+about)\b",
        r"\b(why\s+is|why\s+are|difference\s+between|example\s+of)\b"
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
    {"label": "🔍 Find Products", "message": "Show me popular products"},
    {"label": "💡 Smartphones under 30000", "message": "Show me smartphones under 30000"},
    {"label": "🛒 Show Cart", "message": "Show my cart"},
    {"label": "💳 Payment Help", "message": "How can I pay?"},
    {"label": "📦 Track Order", "message": "Track my order"},
    {"label": "❓ Help", "message": "What can you do?"},
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

    # Extract quantity (digits, or word numbers like "two of them")
    qty_match = re.search(r'\b(\d+)\s*(?:pieces?|units?|qty|quantity|x)\b', text_lower)
    if qty_match:
        entities["quantity"] = int(qty_match.group(1))

    word_numbers = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    }
    # "add two of them" / "add 3 of them" / "two of those"
    if "quantity" not in entities:
        wq = re.search(
            r'\b(add|put|place|buy|purchase|get)\s+(?:the\s+|a\s+)?(\d+|one|two|three|four|five|six|seven|eight|nine|ten)'
            r'\s+(?:more\s+)?(?:of\s+)?(them|those|these|items?|units?)\b',
            text_lower,
        )
        if wq:
            q = wq.group(2)
            entities["quantity"] = int(q) if q.isdigit() else word_numbers.get(q, 1)
            if "position" not in entities:
                entities["position"] = 1  # refers to the last shown results by default

    # Bare "add two" / "add 3" quantity when talking about the current results
    if "quantity" not in entities and re.search(r'\b(add|put|place|buy)\s+(one|two|three|four|five|six|seven|eight|nine|ten)\b', text_lower):
        mq = re.search(r'\b(add|put|place|buy)\s+(one|two|three|four|five|six|seven|eight|nine|ten)\b', text_lower)
        entities["quantity"] = word_numbers.get(mq.group(2), 1)
        if "position" not in entities:
            entities["position"] = 1

    # Quantity from update phrases: "make it two", "set to 3", "quantity to 5"
    if "quantity" not in entities:
        qd = re.search(r'\b(?:update|set|change|make|reduce|increase)\b.{0,20}?\b(?:to|of|as|=)\s*(\d+)\b', text_lower)
        if qd:
            entities["quantity"] = int(qd.group(1))
    if "quantity" not in entities:
        for w, n in word_numbers.items():
            if re.search(r'\b(?:to|of|=|quantity|qty|amount)\s+' + re.escape(w) + r'\b', text_lower) and re.search(r'\b(update|set|change|make|reduce|increase)\b', text_lower):
                entities["quantity"] = n
                break

    # Extract position (1st, 2nd, etc.)
    pos_match = re.search(r'\b(\d+)(?:st|nd|rd|th)\b', text_lower)
    if pos_match:
        entities["position"] = int(pos_match.group(1))

    # Extract word ordinals (first, second, third, last, next)
    if "position" not in entities:
        word_ordinals = {
            "first": 1, "1st": 1,
            "second": 2, "2nd": 2,
            "third": 3, "3rd": 3,
            "fourth": 4, "4th": 4,
            "fifth": 5, "5th": 5,
            "last": "last",
        }
        for word, pos in word_ordinals.items():
            if re.search(r'\b(?:the\s+)?' + re.escape(word) + r'\b', text_lower):
                entities["position"] = pos
                break

    # Extract category
    for alias, category in CATEGORY_ALIASES.items():
        if re.search(r'\b' + re.escape(alias) + r'\b', text_lower):
            entities["category"] = category
            break

    # Extract ordering intent: cheapest / best rated / most sold
    sort = None
    if re.search(r'\b(cheapest|most\s+affordable|lowest\s+priced?|least\s+expensive|budget\s+(?:option|pick))\b', text_lower):
        sort = "price_asc"
    elif re.search(r'\b(best\s+rated|highest\s+rated|top\s+rated|best\s+rating|best\s+reviews?)\b', text_lower):
        sort = "rating_desc"
    elif re.search(r'\b(most\s+sold|top\s+seller|best\s+seller|most\s+popular|most\s+bought)\b', text_lower):
        sort = "sales_desc"
    if sort:
        entities["sort"] = sort

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
        "cheapest", "cheaper", "cheap", "affordable", "expensive", "better",
        "rated", "rating", "budget", "under", "below", "more", "than", "also", "too",
        "something", "anything", "one", "ones", "item", "items", "product",
        "products", "option", "options", "few", "couple", "some",
        "alternatives", "alternative", "deals", "deal", "discount", "discounts",
        "what", "whats", "which", "who", "when", "where", "why", "do", "does",
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

    def _ctx():
        from services.agent_tools import get_session_data
        return get_session_data(session_id)

    if intent == "greeting":
        return {
            "content": (
                "Hello! 👋 I'm the **Commerce Assistant**. I can find and compare products, "
                "recommend accessories, manage your cart, check out via Razorpay TEST MODE, "
                "and explain anything about the store. Try \"show me laptops under 60000\" "
                "or \"what's in my cart?\" — or just ask me a question!"
            ),
            "tool_calls": None,
            "quick_actions": QUICK_ACTIONS,
        }

    if intent == "identity":
        return {
            "content": (
                "I'm the **Commerce Assistant** — the AI assistant of **AI Growth & Commerce Agent**.\n\n"
                "I run on deterministic, explainable rules over this store's real data (no external AI or API keys). "
                "I can:\n\n"
                "🔍 Search & compare real products\n"
                "🛒 Manage your shared cart (add, update quantity, remove)\n"
                "💡 Recommend upsells, accessories and cheaper alternatives\n"
                "💳 Explain payments and guide you through Razorpay TEST MODE checkout\n"
                "📦 Look up orders and answer questions about the store\n\n"
                "What would you like to do?"
            ),
            "tool_calls": None,
            "quick_actions": QUICK_ACTIONS,
        }

    if intent == "security_refusal":
        return {
            "content": (
                "I can't share internal credentials, API keys, secrets or system prompts — "
                "those stay private on the server and are never exposed to users. 🔒\n\n"
                "I'm also a bounded demo agent: I can only act through approved commerce tools "
                "(catalog, cart, checkout), and every money action follows policy limits and "
                "requires approval. If you'd like to configure payment keys, use the Settings "
                "page. Anything else I can help you with?"
            ),
            "tool_calls": None,
            "quick_actions": [
                {"label": "Find Products", "message": "Show me popular products"},
                {"label": "Help", "message": "Help"},
            ],
        }

    if intent == "payment_failed":
        return {
            "content": (
                "Sorry your payment didn't go through! 😕 Here's what happens and what you can do:\n\n"
                "• Your order is **NOT** marked as paid and no money is charged (Razorpay TEST MODE).\n"
                "• Your cart and order are kept safe — inventory is only reduced on a *verified* success.\n"
                "• The failure is recorded in the audit trail with the reason.\n\n"
                "To retry: open the order again and tap **Pay with Razorpay**, or just say \"checkout\" "
                "and I'll start a fresh payment for the same cart. If it keeps failing, try a different "
                "test card/UPI or check your connection."
            ),
            "tool_calls": None,
            "quick_actions": [
                {"label": "Checkout", "message": "checkout"},
                {"label": "Show Cart", "message": "Show my cart"},
            ],
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
        # Resolve which item: ordinal position ("the last item"), the product just
        # added, or a product named in the message.
        position = entities.get("position")
        product_name = None
        q = entities.get("query", "")
        if q:
            junk = {"remove", "delete", "drop", "take", "off", "cart", "item", "items", "out",
                     "first", "second", "third", "fourth", "fifth", "last", "one", "the"}
            cleaned = " ".join(w for w in q.split() if w not in junk)
            if cleaned:
                product_name = cleaned
        return {
            "content": None,
            "tool_calls": [{"name": "remove_cart_item", "arguments": {
                "product_position": position,
                "product_name": product_name,
            }}],
        }

    if intent == "clear_cart":
        return {
            "content": None,
            "tool_calls": [{"name": "clear_cart", "arguments": {}}],
        }

    if intent == "update_cart_qty":
        qty = entities.get("quantity") or 1
        return {
            "content": None,
            "tool_calls": [{"name": "update_cart_quantity", "arguments": {
                "quantity": qty,
                "product_position": entities.get("position"),
            }}],
        }

    if intent == "accessories":
        # "What accessories go with the second one?" → cross-sell for the product in context
        return {
            "content": None,
            "tool_calls": [{"name": "recommend_cross_sell", "arguments": {
                "product_id": entities.get("product_id"),
                "product_position": entities.get("position"),
            }}],
        }

    if intent == "cheaper_alternative":
        ctx = _ctx()
        has_context = bool(ctx.get("last_search_results"))
        names_product = bool(entities.get("category") or entities.get("query"))
        if has_context and not names_product:
            # "Show me cheaper alternatives" → alternatives to the product in context
            return {
                "content": None,
                "tool_calls": [{"name": "get_cheaper_alternatives", "arguments": {
                    "product_id": entities.get("product_id"),
                    "product_position": entities.get("position"),
                }}],
            }
        if names_product:
            # "What is the cheapest laptop?" → real search sorted by price ascending
            return {
                "content": None,
                "tool_calls": [{"name": "search_products", "arguments": {
                    "query": entities.get("query", ""),
                    "category": entities.get("category"),
                    "max_price": entities.get("max_price"),
                    "min_price": entities.get("min_price"),
                    "in_stock": True,
                    "sort": entities.get("sort") or "price_asc",
                }}],
            }
        return {
            "content": "I can find cheaper alternatives for you, but I need a product in context first — please search for a product first (e.g. \"show me headphones\"), then ask me for cheaper alternatives.",
            "tool_calls": None,
            "quick_actions": [
                {"label": "Find Products", "message": "Show me popular products"},
            ],
        }

    if intent == "checkout":
        return {
            "content": None,
            "tool_calls": [{"name": "create_checkout", "arguments": {}}],
        }

    if intent == "order_status":
        ctx = _ctx()
        order_info = ""
        if db is not None:
            try:
                from sqlalchemy import select as _sel
                from models.models import Order as _Order, Cart as _Cart
                q = await db.execute(
                    _sel(_Order).join(_Cart, _Order.cart_id == _Cart.id)
                    .where(_Cart.session_id == session_id)
                    .order_by(_Order.created_at.desc()).limit(1)
                )
                latest = q.scalar_one_or_none()
                if latest:
                    sid = str(latest.id)[:8].upper()
                    order_info = (
                        f"\n\nYour most recent order is **#{sid}** — status: **{latest.status}**, "
                        f"payment: **{latest.payment_status}** (₹{latest.total:,.0f}). "
                        "You can see full details on the Orders page."
                    )
            except Exception as e:
                logger.warning(f"order_status lookup skipped: {e}")
        return {
            "content": "Here's how to track an order: open the **Orders** page to see every order with its payment status." + order_info,
            "tool_calls": None,
            "quick_actions": [
                {"label": "View Orders", "message": "Show my orders"},
            ],
        }

    if intent == "best_sellers":
        return {
            "content": None,
            "tool_calls": [{"name": "get_bestsellers", "arguments": {"limit": 5}}],
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
        # Context comparison: if the last search returned products, compare the
        # top options from real result data (no invented specs).
        ctx = _ctx()
        results = ctx.get("last_search_results", [])
        if len(results) >= 2:
            pos = entities.get("position")
            idx1 = 0
            idx2 = 1
            if isinstance(pos, int) and 1 <= pos < len(results):
                idx2 = pos
            a, b = results[idx1], results[idx2]
            ra = (a.get("rating") or 0)
            rb = (b.get("rating") or 0)
            sa = (a.get("sales") or 0)
            sb = (b.get("sales") or 0)
            pa = a.get("price") or 0
            pb = b.get("price") or 0

            def line(p):
                return (
                    f"**{p.get('name')}** — ₹{p.get('price'):,.0f}\n"
                    f"• Rating: {p.get('rating') or '—'}/5 • Units sold: {p.get('sales') or 0}\n"
                    f"• {p.get('category') or ''}{((' — ' + p.get('subcategory')) if p.get('subcategory') else '')}\n"
                    f"• {p.get('brand') or 'Store brand'}"
                )

            text = "Here's how they compare:\n\n"
            text += f"**1.** {line(a)}\n\n**2.** {line(b)}\n\n"
            # Deterministic pick based on what the shopper actually asked
            tl = ((ctx.get("current_message") or "") or "").lower()
            if not tl:
                user_msgs = [m.get("content", "") for m in (ctx.get("conversation_history") or []) if m.get("role") == "user"]
                tl = (user_msgs[-1] if user_msgs else "").lower()
            if "cheap" in tl:
                pick = a if pa <= pb else b
                text += f"Looking for the budget pick? **{pick.get('name')}** is cheaper at ₹{pick.get('price'):,.0f}."
            elif "rating" in tl or "review" in tl:
                pick = a if ra >= rb else b
                text += f"By rating, **{pick.get('name')}** leads at {pick.get('rating') or 0}/5."
            else:
                pick = a if sa >= sb else b
                text += f"By popularity, **{pick.get('name')}** has sold more ({pick.get('sales') or 0} units)."
            return {
                "content": text,
                "tool_calls": None,
                "quick_actions": [
                    {"label": "Add First", "message": "add the first one to cart"},
                    {"label": "Add Second", "message": "add the second one to cart"},
                ],
            }
        return {
            "content": "I can compare products for you! First search something like \"show me laptops\", then ask \"which one is better?\" and I'll compare the options from the real catalog.",
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
                "sort": entities.get("sort"),
                }}],
            }
        return {
            "content": None,
            "tool_calls": [{"name": "search_products", "arguments": {
                "query": "popular trending",
                "in_stock": True,
                "sort": entities.get("sort"),
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
                "sort": entities.get("sort"),
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
                "sort": entities.get("sort"),
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
                "sort": entities.get("sort"),
            }}],
        }

    if intent == "stock_query":
        ctx = _ctx()
        results = ctx.get("last_search_results", [])
        if results:
            lines = []
            for p in results[:5]:
                stock = p.get("stock") or 0
                status = "✅ In stock" if stock > 5 else ("⚠️ Low stock" if stock > 0 else "❌ Out of stock")
                lines.append(f"• **{p.get('name')}** — {status} ({stock} units)")
            return {
                "content": "Here's the availability of the products we were looking at:\n\n" + "\n".join(lines),
                "tool_calls": None,
            }
        return {
            "content": "All products shown are currently in stock. Looking for something specific? Tell me what you need and I'll check its availability.",
            "tool_calls": None,
        }

    if intent == "product_details":
        ctx = _ctx()
        results = ctx.get("last_search_results", [])
        pos = entities.get("position") or 1
        if results and isinstance(pos, int) and 1 <= pos <= len(results):
            p = results[pos - 1]
            content = (
                f"**{p.get('name')}**\n\n"
                f"{(p.get('description') or 'No description available.')[:280]}\n\n"
                f"💰 Price: **₹{p.get('price'):,.0f}**"
                + (f" ~~₹{p.get('previous_price'):,.0f}~~" if p.get("previous_price") else "")
                + f"\n🏷️ Category: {p.get('category') or '—'}" + (f" / {p.get('subcategory')}" if p.get("subcategory") else "")
                + f"\n⭐ Rating: {p.get('rating') or '—'}/5"
                + f"\n📦 In stock: {p.get('stock') or 0} units"
                + f"\n🏢 Brand: {p.get('brand') or 'Store brand'}"
            )
            return {
                "content": content,
                "tool_calls": None,
                "quick_actions": [
                    {"label": "Add to Cart", "message": "add the first one to cart"},
                    {"label": "Accessories", "message": "What accessories go with this?"},
                    {"label": "Cheaper Options", "message": "Show me cheaper alternatives"},
                ],
            }
        return {
            "content": "Tell me which product you'd like to know more about — search for something first (e.g. \"show me headphones\"), then ask \"tell me about the first one\".",
            "tool_calls": None,
            "quick_actions": [
                {"label": "Find Products", "message": "Show me popular products"},
            ],
        }

    if intent == "general_chat":
        ctx = _ctx()
        text = (ctx.get("current_message") or "").strip()
        if not text:
            user_msgs = [m.get("content", "") for m in (ctx.get("conversation_history") or []) if m.get("role") == "user"]
            text = (user_msgs[-1] if user_msgs else "") or ""
        # Try the knowledge bank, then the FAQ block, then be honest.
        kb = answer_general_question(text)
        if kb:
            return {"content": kb, "tool_calls": None, "quick_actions": QUICK_ACTIONS}
        for faq in FAQ_RESPONSES.values():
            if any(kw in text.lower() for kw in faq["keywords"]):
                return {"content": faq["response"], "tool_calls": None}
        if re.search(r"\b(you|yourself|assistant|bot)\b", text.lower()):
            return {
                "content": "I'm the Commerce Assistant — an explainable rule-based assistant for this demo store. I search the real catalog, manage your shared cart, and explain payments, orders and growth features. Ask me anything about the store!",
                "tool_calls": None,
                "quick_actions": QUICK_ACTIONS,
            }
        return {
            "content": "I don't have enough information to answer that accurately — I'm a commerce-focused assistant and I never invent facts. 😊\n\nI **can** help you with products, prices, availability, your cart, orders, payments, and explain how this store works.",
            "tool_calls": None,
            "quick_actions": QUICK_ACTIONS,
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
                "sort": entities.get("sort"),
            }}],
        }

    return {
        "content": (
            "I can help you find and compare products, manage your cart, place orders via Razorpay TEST MODE, "
            "and explain anything about the store. If you have a question I haven't covered, feel free to "
            "rephrase it — or try one of these:\n\n"
            "• \"What is Razorpay?\"\n"
            "• \"Show me laptops under ₹60,000\"\n"
            "• \"What's in my cart?\""
        ),
        "tool_calls": None,
        "quick_actions": QUICK_ACTIONS,
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
