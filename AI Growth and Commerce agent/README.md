# MerchantFlow AI

AI Growth & Agentic Commerce Agent for Razorpay AI Buildathon

## Quick Start

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python seed.py
uvicorn main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Access

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Features

1. **AI Shopping Assistant** - Chat interface for product discovery
2. **Product Catalog** - Agent-readable catalog with 30+ products
3. **Cart System** - Add products and calculate totals
4. **Policy Engine** - Spending limits and approval requirements
5. **Approval Gate** - Explicit payment approval workflow
6. **Razorpay Integration** - Test mode payment processing
7. **Audit Trail** - Complete logging of all agent actions
8. **Merchant Dashboard** - Growth analytics and metrics
9. **Failure Demo** - Graceful handling of payment failures

## Demo Flow

1. Visit `/buyer` and ask "Find me headphones under ₹3000"
2. Agent searches catalog and presents products
3. Accept a cross-sell recommendation
4. View cart with calculated total
5. Approve payment (policy check runs)
6. Process payment via Razorpay test mode
7. View audit trail at `/audit`
8. Demo payment failure at `/payments`

## Safety Architecture

```
AI Agent → Tool Call → Backend → Policy Engine → Approval Gate → Razorpay Test API
```

- AI cannot access Razorpay secrets
- All financial calculations by backend
- Spending limits enforced
- Explicit approval required
- Complete audit trail

## Environment Variables

Create `backend/.env`:

```
RAZORPAY_KEY_ID=rzp_test_your_key
RAZORPAY_KEY_SECRET=your_secret
```

Get test credentials from https://dashboard.razorpay.com
