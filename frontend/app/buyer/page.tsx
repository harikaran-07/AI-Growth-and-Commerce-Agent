'use client'

import { useState, useRef, useEffect } from 'react'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  products?: Product[]
  recommendations?: Recommendation[]
  cart?: CartInfo
  approval?: ApprovalInfo
  paymentStatus?: string
  toolCalls?: ToolCall[]
}

interface Product {
  product_id: string
  name: string
  description: string
  category: string
  price: number
  currency: string
  stock: number
  position?: number
}

interface Recommendation {
  product_id: string
  name: string
  price: number
  reason: string
  type: string
}

interface CartInfo {
  cart_id: string
  total: number
  item_count: number
  items?: any[]
}

interface ApprovalInfo {
  approval_id: string
  order_id: string
  status: string
  total: number
  message: string
}

interface ToolCall {
  tool: string
  arguments: any
  result_summary: string
}

interface ChatResponse {
  message: string
  products: Product[]
  recommendations: Recommendation[]
  cart: CartInfo | null
  approval: ApprovalInfo | null
  payment: any
  tool_calls: ToolCall[]
}

export default function BuyerPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId] = useState(() => `session_${Date.now()}`)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    const messageText = input.trim()
    if (!messageText || loading) return

    const userMessage: Message = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: messageText
    }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch('/api/agent/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: messageText,
          session_id: sessionId
        })
      })

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(errorData.detail || `HTTP ${res.status}`)
      }

      const data: ChatResponse = await res.json()

      const assistantMessage: Message = {
        id: `msg_${Date.now() + 1}`,
        role: 'assistant',
        content: data.message,
        products: data.products?.length ? data.products : undefined,
        recommendations: data.recommendations?.length ? data.recommendations : undefined,
        cart: data.cart || undefined,
        approval: data.approval || undefined,
        toolCalls: data.tool_calls?.length ? data.tool_calls : undefined
      }
      setMessages(prev => [...prev, assistantMessage])

      // If there's an approval, save it for later
      if (data.approval) {
        setPendingApproval(data.approval)
      }
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage: Message = {
        id: `msg_${Date.now() + 1}`,
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}. Please try again.`
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const [pendingApproval, setPendingApproval] = useState<ApprovalInfo | null>(null)

  const handleApprovePayment = async () => {
    if (!pendingApproval) return
    setLoading(true)

    try {
      // 1. Approve the approval
      const approveRes = await fetch(`/api/approvals/${pendingApproval.approval_id}/approve`, {
        method: 'POST'
      })

      if (!approveRes.ok) {
        const err = await approveRes.json().catch(() => ({}))
        throw new Error(err.detail || 'Approval failed')
      }

      // 2. Create payment
      const paymentRes = await fetch('/api/payments/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ order_id: pendingApproval.order_id })
      })

      if (!paymentRes.ok) {
        const err = await paymentRes.json().catch(() => ({}))
        throw new Error(err.detail || 'Payment creation failed')
      }

      const paymentData = await paymentRes.json()

      const paymentMessage: Message = {
        id: `msg_${Date.now()}`,
        role: 'assistant',
        content: paymentData.status === 'initiated'
          ? `✅ Payment initiated successfully!\n\nOrder ID: ${paymentData.order_id}\nPayment Status: Processing...\nRazorpay Order: ${paymentData.razorpay_order_id}\n\nThe payment is being processed. You can check the status in the Payments tab.`
          : `❌ Payment failed: ${paymentData.failure_reason || 'Unknown error'}\n\nYou can try again or check the Payments tab for details.`,
        paymentStatus: paymentData.status
      }
      setMessages(prev => [...prev, paymentMessage])
      setPendingApproval(null)
    } catch (error) {
      console.error('Payment error:', error)
      const errorMessage: Message = {
        id: `msg_${Date.now()}`,
        role: 'assistant',
        content: `Payment error: ${error instanceof Error ? error.message : 'Unknown error'}. Please try again.`
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleAddProduct = async (productPosition?: number, productId?: string) => {
    setLoading(true)
    try {
      const args: any = { quantity: 1 }
      if (productId) args.product_id = productId
      else if (productPosition) args.product_position = productPosition

      const res = await fetch('/api/agent/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: productId
            ? `Add product ${productId} to my cart`
            : `Add the ${productPosition === 1 ? 'first' : productPosition === 2 ? 'second' : productPosition === 3 ? 'third' : `${productPosition}th`} product to my cart`,
          session_id: sessionId
        })
      })

      if (!res.ok) throw new Error('Failed to add to cart')

      const data: ChatResponse = await res.json()

      const assistantMessage: Message = {
        id: `msg_${Date.now()}`,
        role: 'assistant',
        content: data.message,
        cart: data.cart || undefined,
        approval: data.approval || undefined,
        recommendations: data.recommendations?.length ? data.recommendations : undefined
      }
      setMessages(prev => [...prev, assistantMessage])

      if (data.approval) {
        setPendingApproval(data.approval)
      }
    } catch (error) {
      const errorMessage: Message = {
        id: `msg_${Date.now()}`,
        role: 'assistant',
        content: 'Failed to add product to cart. Please try again.'
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <h1 className="text-xl font-bold text-gray-900">AI Shopping Assistant</h1>
        <p className="text-sm text-gray-600">Powered by LLM Agent with tool calling</p>
        <div className="flex items-center gap-2 mt-1">
          <span className="inline-block px-2 py-0.5 bg-green-100 text-green-800 text-xs font-medium rounded">
            AI AGENT
          </span>
          <span className="text-xs text-gray-500">Session: {sessionId.slice(0, 20)}...</span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-auto p-6 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🤖</div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Welcome to MerchantFlow AI</h2>
            <p className="text-gray-600 mb-6">I can help you find products, make recommendations, and complete purchases.</p>
            <div className="flex flex-wrap justify-center gap-2 max-w-xl mx-auto">
              {[
                'Find headphones under ₹3000',
                'Show me laptop accessories',
                'I need a wireless mouse',
                'What do you recommend?'
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => { setInput(suggestion); }}
                  className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-full text-sm text-gray-700 transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-2xl rounded-lg px-4 py-3 ${
                message.role === 'user'
                  ? 'bg-primary-600 text-white'
                  : 'bg-white border shadow-sm'
              }`}
            >
              <div className="whitespace-pre-wrap text-sm">{message.content}</div>

              {/* Product cards */}
              {message.products && message.products.length > 0 && (
                <div className="mt-4 space-y-2">
                  {message.products.map((product) => (
                    <div key={product.product_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs bg-primary-100 text-primary-800 px-2 py-0.5 rounded">
                            #{product.position}
                          </span>
                          <p className="font-medium text-gray-900">{product.name}</p>
                        </div>
                        <p className="text-xs text-gray-500 mt-1">{product.description?.slice(0, 80)}...</p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-sm font-bold text-primary-600">₹{product.price.toLocaleString()}</span>
                          <span className="text-xs text-gray-500">{product.category}</span>
                          <span className={`text-xs px-1.5 py-0.5 rounded ${product.stock > 10 ? 'bg-green-100 text-green-700' : product.stock > 0 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}`}>
                            {product.stock > 0 ? `${product.stock} in stock` : 'Out of stock'}
                          </span>
                        </div>
                      </div>
                      {product.stock > 0 && (
                        <button
                          onClick={() => handleAddProduct(product.position, product.product_id)}
                          className="ml-3 px-3 py-1.5 bg-primary-600 text-white text-sm rounded hover:bg-primary-700 whitespace-nowrap"
                        >
                          Add to Cart
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Recommendations */}
              {message.recommendations && message.recommendations.length > 0 && (
                <div className="mt-3 p-3 bg-blue-50 rounded-lg">
                  <p className="text-sm font-medium text-blue-900 mb-2">💡 Recommended Add-ons:</p>
                  {message.recommendations.map((rec) => (
                    <div key={rec.product_id} className="flex items-center justify-between py-1.5">
                      <div className="flex-1">
                        <span className="text-sm font-medium">{rec.name}</span>
                        <span className="text-sm text-gray-600 ml-2">₹{rec.price.toLocaleString()}</span>
                        {rec.reason && (
                          <p className="text-xs text-blue-700 mt-0.5">{rec.reason}</p>
                        )}
                      </div>
                      <button
                        onClick={() => handleAddProduct(undefined, rec.product_id)}
                        className="ml-2 text-xs text-primary-600 hover:underline font-medium"
                      >
                        + Add
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Cart summary */}
              {message.cart && (
                <div className="mt-4 pt-4 border-t">
                  <div className="bg-gray-50 p-3 rounded-lg mb-3">
                    <p className="text-sm font-medium text-gray-900">🛒 Cart Summary</p>
                    <p className="text-lg font-bold text-primary-600 mt-1">
                      ₹{message.cart.total.toLocaleString()}
                      <span className="text-sm font-normal text-gray-500 ml-2">
                        ({message.cart.item_count} item{message.cart.item_count !== 1 ? 's' : ''})
                      </span>
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      const lastProductMsg = [...messages].reverse().find(m => m.products?.length)
                      if (lastProductMsg) {
                        setInput('How much is my cart?')
                      } else {
                        setInput('Check my cart total')
                      }
                    }}
                    className="w-full px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 text-sm"
                  >
                    View Cart & Proceed to Payment
                  </button>
                </div>
              )}

              {/* Approval pending */}
              {message.approval && (
                <div className="mt-4 pt-4 border-t">
                  <div className="bg-yellow-50 p-3 rounded-lg mb-3">
                    <p className="text-sm font-medium text-yellow-800">⚠️ Approval Required</p>
                    <p className="text-xs text-yellow-700 mt-1">
                      Total: ₹{message.approval.total.toLocaleString()} — This payment requires your explicit approval.
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={handleApprovePayment}
                      className="flex-1 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm font-medium"
                    >
                      ✓ Approve Payment
                    </button>
                    <button
                      onClick={() => setPendingApproval(null)}
                      className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 text-sm"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}

              {/* Payment status */}
              {message.paymentStatus && (
                <div className={`mt-3 p-3 rounded ${
                  message.paymentStatus === 'initiated' ? 'bg-blue-50' : 'bg-red-50'
                }`}>
                  <p className={`text-sm font-medium ${
                    message.paymentStatus === 'initiated' ? 'text-blue-800' : 'text-red-800'
                  }`}>
                    {message.paymentStatus === 'initiated'
                      ? '✅ Payment Processing'
                      : '❌ Payment Failed'}
                  </p>
                </div>
              )}

              {/* Tool calls (debug) */}
              {message.toolCalls && message.toolCalls.length > 0 && process.env.NODE_ENV === 'development' && (
                <details className="mt-3 text-xs text-gray-500">
                  <summary className="cursor-pointer hover:text-gray-700">Tool calls ({message.toolCalls.length})</summary>
                  <div className="mt-1 space-y-1">
                    {message.toolCalls.map((tc, i) => (
                      <div key={i} className="bg-gray-100 p-2 rounded">
                        <span className="font-mono">{tc.tool}</span>
                        <span className="ml-2 text-gray-400">→ {tc.result_summary?.slice(0, 80)}</span>
                      </div>
                    ))}
                  </div>
                </details>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border rounded-lg px-4 py-3 shadow-sm">
              <div className="flex items-center gap-2">
                <div className="text-sm text-gray-600">Thinking</div>
                <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t bg-white p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder="Ask me to find products, add to cart, check out..."
            className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {loading ? '...' : 'Send'}
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2 text-center">
          Powered by AI Agent • Products from TechZone Electronics catalog • TEST MODE
        </p>
      </div>
    </div>
  )
}
