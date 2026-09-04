 AI Growth & Commerce Agent

> AI-powered merchant growth and agentic commerce platform built for the Razorpay AI Growth & Agentic Commerce challenge.**

Live Demo:[https://ai-growth-and-commerce-agent.onrender.com](https://ai-growth-and-commerce-agent.onrender.com)
GitHub: [https://github.com/harikaran-07/AI-Growth-and-Commerce-Agent](https://github.com/harikaran-07/AI-Growth-and-Commerce-Agent)

---

🚀 Overview

**AI Growth & Commerce Agent** is an AI-powered commerce platform designed to help merchants **grow revenue** while making their products **discoverable and transactable by AI buyers**.

The platform combines:

* 🤖 Conversational AI Commerce Assistant
* 🛍️ Agent-readable product catalog
* 💡 AI-powered product recommendations
* 📈 Merchant growth insights
* 🎯 Campaign orchestration
* 🛒 Shared real-time shopping cart
* 💳 Razorpay TEST MODE checkout
* 📦 Order & payment management
* 🔐 Policy-controlled commerce actions
* 🧾 Complete audit trail

The goal is to demonstrate an end-to-end flow:

```text
AI Buyer
   ↓
Discover Products
   ↓
AI Recommendation
   ↓
Add to Cart
   ↓
Checkout
   ↓
Razorpay TEST MODE
   ↓
Payment Verification
   ↓
Order Creation
   ↓
Audit Trail
```

And for merchants:

```text
Merchant Data
     ↓
Growth Analysis
     ↓
Revenue Opportunity
     ↓
Campaign Proposal
     ↓
Policy Check
     ↓
Merchant Approval
     ↓
Campaign Execution
     ↓
Audit Trail
```

---

## 🎯 Problem

Traditional e-commerce platforms mainly depend on users manually browsing products, comparing specifications and completing checkout.

At the same time, AI agents are increasingly becoming an interface between customers and commerce.

Merchants therefore need a system where:

1. AI can understand customer requirements.
2. AI can discover products from a structured catalog.
3. AI can recommend products based on specifications and user intent.
4. AI can manage carts and initiate checkout.
5. Payments remain secure and controlled.
6. Merchant growth actions are explainable and bounded.
7. Every important action can be audited.

**AI Growth & Commerce Agent** addresses these requirements in one platform.

---

# ✨ Key Features

## 🤖 Commerce Assistant

A conversational AI shopping assistant that understands natural-language requests.

Example:

> "I need a gaming laptop under ₹70,000 with 16GB RAM."

The assistant can:

* Understand user requirements
* Search products
* Analyze specifications
* Recommend suitable products
* Explain why a product matches
* Compare products
* Find cheaper alternatives
* Recommend accessories
* Add products to cart
* Update quantities
* Start checkout
* Help with payment and orders

Example conversation:

```text
User:
I need a phone under ₹30,000 with a good camera.

Assistant:
I found several matching phones.

Product A
• 256GB Storage
• 50MP Camera
• 5G
• ₹28,999

Why I recommend it:
It matches your budget, storage and camera requirements.
```

---

# 🧠 Intelligent Product Recommendations

Recommendations are based on the user's actual requirements instead of simply returning random products.

The assistant considers:

* Budget
* Category
* Use case
* Product specifications
* Availability
* Rating
* Value for money

For example:

```text
User requirements
       ↓
Budget
Use Case
Specifications
Features
       ↓
Product Matching
       ↓
Ranking
       ↓
Recommendation
```

The assistant also maintains conversational context.

Example:

```text
User: Show me phones under ₹30,000.

Assistant: [Products]

User: Which one is better for gaming?

Assistant: [Comparison]

User: Add the best one.

Assistant: Added the selected product to your cart.
```

---

# 🛍️ Agent-Readable Catalog

Products are available through structured, machine-readable catalog data.

Each product has stable information such as:

```text
Product ID
Product Name
Category
Price
Stock
Availability
Image URL
Product URL
Specifications
```

This allows AI agents to discover and reason about products without depending only on visual UI elements.

---

# 🛒 Shared Shopping Cart

The platform uses one shared cart across:

* Product pages
* Product cards
* Commerce Assistant
* Cart page
* Checkout

Supported actions:

* Add product
* Remove product
* Update quantity
* View cart
* Calculate total
* Checkout

Cart changes are reflected immediately across the application.

---

# 💳 Razorpay TEST MODE Payments

The project integrates Razorpay TEST MODE for the checkout flow.

Payment architecture:

```text
Cart
 ↓
Backend Order Creation
 ↓
Razorpay TEST MODE
 ↓
Checkout
 ↓
Payment
 ↓
Signature Verification
 ↓
Order Confirmation
```

The backend verifies the payment before marking an order as successful.

### Security

Razorpay credentials are stored using environment variables:

```env
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
```

Secrets are never stored in the frontend or committed to GitHub.

---

# 📦 Orders & Payments

The application maintains order and payment information including:

* Order ID
* Razorpay Order ID
* Razorpay Payment ID
* Products
* Quantity
* Amount
* Currency
* Payment status
* Order status
* Timestamp

The dashboard can use transaction data to calculate:

* Total orders
* Revenue
* Successful payments
* Average order value
* Payment success rate

---

# 📈 Merchant Growth Intelligence

The merchant dashboard provides AI-assisted growth insights.

The system can analyze merchant data and identify opportunities involving:

* Revenue
* Products
* Customers
* Orders
* Product performance
* Growth opportunities
* Recommendations

The objective is to help merchants move from:

```text
Data
 ↓
Insight
 ↓
Opportunity
 ↓
Action
```

---

# 🎯 Campaign Orchestrator

The platform includes a controlled campaign workflow:

```text
Campaign Proposal
       ↓
Policy Check
       ↓
Merchant Approval
       ↓
Execution
       ↓
Result
       ↓
Audit Trail
```

Campaign actions are not automatically executed without the appropriate controls.

This helps ensure that AI-driven merchant actions are:

* Explainable
* Bounded
* Approval-aware
* Auditable

---

# 🔐 Safety & Audit Trail

Every important commerce action can be recorded in the audit trail.

Examples:

```text
Product Search
Cart Modification
Checkout Creation
Payment Initiation
Payment Verification
Order Creation
Campaign Proposal
Policy Decision
Merchant Approval
Campaign Execution
```

The system is designed around:

> **Every money action should be explainable, bounded and gated.**

---

# 🧩 Architecture

```text
                    ┌───────────────────────┐
                    │      User / AI Buyer  │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Commerce Assistant  │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │  AI / Intent Layer   │
                    └───────────┬───────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
        Product Search      Cart Tools      Recommendations
              │                 │                 │
              └─────────────────┼─────────────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │      Backend API    │
                     │       FastAPI       │
                     └──────────┬──────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
          Products           Orders           Payments
                                                  │
                                                  ▼
                                         Razorpay TEST MODE

                         Merchant Side
                              │
                              ▼
                     Growth Intelligence
                              │
                              ▼
                     Campaign Orchestrator
                              │
                              ▼
                       Policy / Approval
                              │
                              ▼
                         Audit Trail
```

---

# 🛠️ Technology Stack

## Frontend

* React
* TypeScript
* Tailwind CSS
* Modern responsive UI
* Component-based architecture

## Backend

* Python
* FastAPI
* REST APIs
* Pydantic

## Payments

* Razorpay TEST MODE

## AI

* Conversational AI architecture
* Tool-based commerce actions
* Natural-language product recommendations

## Deployment

* Render
* GitHub

---

# 📂 Project Structure

```text
AI-Growth-and-Commerce-Agent/
│
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── ...
│
├── frontend/
│   ├── components/
│   ├── pages/
│   ├── ...
│
├── README.md
├── .gitignore
└── ...
```

---

# ⚙️ Local Setup

## 1. Clone the repository

```bash
git clone https://github.com/harikaran-07/AI-Growth-and-Commerce-Agent.git
cd AI-Growth-and-Commerce-Agent
```

## 2. Backend setup

```bash
cd backend
pip install -r requirements.txt
```

Create your environment variables:

```env
RAZORPAY_KEY_ID=your_test_key_id
RAZORPAY_KEY_SECRET=your_test_key_secret
```

Run the backend:

```bash
uvicorn main:app --reload
```

---

## 3. Frontend setup

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

The application will be available through the local development URL shown by Vite.

---

# 🌐 Live Deployment

### Production Demo

[https://ai-growth-and-commerce-agent.onrender.com](https://ai-growth-and-commerce-agent.onrender.com)

### GitHub Repository

[https://github.com/harikaran-07/AI-Growth-and-Commerce-Agent](https://github.com/harikaran-07/AI-Growth-and-Commerce-Agent)

---

# 🧪 Testing

The project includes backend tests covering important application functionality.

Key areas tested include:

* Product APIs
* Product search
* Cart operations
* Checkout
* Payment verification
* Order handling
* Recommendations
* Campaign workflows
* Policy controls
* Audit logging

Run backend tests with:

```bash
pytest
```

---

# 💰 Razorpay Test Mode

This project uses **Razorpay TEST MODE**.

No real money should be used for testing.

For demonstration:

```text
Product
   ↓
Cart
   ↓
Checkout
   ↓
Razorpay TEST MODE
   ↓
Payment
   ↓
Verification
   ↓
Order
```

---

# 🏆 Buildathon Alignment

This project targets the **AI Growth & Agentic Commerce** challenge.

### Conversational In-App Checkout

Users can discover products, manage their cart and proceed toward payment through conversational interaction.

### Agent-Readable Catalog

Products are exposed in structured data suitable for AI discovery.

### Upsell & Cross-Sell

The assistant can recommend relevant products and accessories based on user context.

### Campaign Orchestrator

Merchants can propose, approve and execute controlled growth campaigns.

### Explainable Commerce

Payment and merchant actions are bounded and recorded through policy and audit mechanisms.

---

# 🎬 Suggested Demo Flow

For a buildathon presentation:

### 1. AI Product Discovery

Ask:

> "I need a gaming laptop under ₹70,000."

Show the AI recommendation and specifications.

### 2. Product Comparison

Ask:

> "Which one is better for gaming?"

Show the specification comparison.

### 3. Cart

Ask:

> "Add the best one to my cart."

Show the shared cart updating.

### 4. Checkout

Ask:

> "Checkout."

Open Razorpay TEST MODE.

### 5. Payment

Complete the test payment.

### 6. Order

Show the generated order.

### 7. Audit Trail

Show:

```text
Checkout Created
Payment Initiated
Payment Verified
Order Created
Order Confirmed
```

### 8. Merchant Growth

Open the Growth/Campaign section.

Show:

```text
Opportunity
   ↓
Campaign Proposal
   ↓
Policy Check
   ↓
Merchant Approval
   ↓
Execution
```

---

# 🔒 Security

* Razorpay secrets stored in environment variables
* No secret keys in frontend
* Server-side payment verification
* Input validation
* Controlled commerce actions
* Policy checks
* Audit logging
* Duplicate transaction protection
* Graceful payment failure handling

---

# 🚀 Future Improvements

Possible future extensions:

* AI buyer protocol integrations
* More advanced merchant revenue prediction
* Personalized recommendations
* Automated A/B campaign optimization
* Real-time inventory intelligence
* Multi-agent commerce workflows
* Advanced customer segmentation
* Additional payment and commerce protocols

---

# 👨‍💻 Author

**R. Harikaran**

AI/ML & Software Development Enthusiast

GitHub:
[https://github.com/harikaran-07](https://github.com/harikaran-07)

---

## ⭐ Project Vision

**AI Growth & Commerce Agent** aims to bridge the gap between **AI agents, merchants and payments**.

```text
AI understands the customer
          ↓
AI discovers the right product
          ↓
AI recommends the best option
          ↓
AI manages the cart
          ↓
Razorpay handles payment
          ↓
Merchant receives the order
          ↓
AI helps the merchant grow
```

> **Making commerce conversational, agent-ready, explainable and transactable.**
