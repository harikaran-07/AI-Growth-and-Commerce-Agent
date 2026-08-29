'use client'

import { useState, useRef, useEffect } from 'react'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  products?: Product[]
  recommendations?: Recommendation[]
  cartId?: string
  total?: number
  approvalPending?: boolean
  paymentStatus?: string
}

interface Product {
  product_id: string
  name: string
  description: string
  category: string
  price: number
  currency: string
  stock: number
}

interface Recommendation {
  product_id: string
  name: string
  price: number
  reason: string
  type: string
}

export default function BuyerPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId] = useState(() => `session_${Date.now()}`)
  const [cartId, setCartId] = useState<string | null>(null)
  const [cartTotal, setCartTotal] = useState(0)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage: Message = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: input
    }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const searchRes = await fetch('/api/agent/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: input,
          session_id: sessionId
        })
      })
      const searchData = await searchRes.json()

      let responseContent = ''
      let products: Product[] = []
      let recommendations: Recommendation[] = []

      if (searchData.products && searchData.products.length > 0) {
        products = searchData.products
        responseContent = `I found ${products.length} product(s) matching your request:\n\n`
        products.forEach((p: Product) => {
          responseContent += `• ${p.name} - ₹${p.price.toLocaleString()} (${p.stock} in stock)\n`
        })

        if (searchData.recommendations && searchData.recommendations.length > 0) {
          recommendations = searchData.recommendations
          responseContent += '\n💡 Based on your selection, you might also like:\n'
          recommendations.forEach((r: Recommendation) => {
            responseContent += `• ${r.name} - ₹${r.price.toLocaleString()}\n  Reason: ${r.reason}\n`
          })
        }

        responseContent += '\nWould you like me to add any of these to your cart?'
      } else {
        responseContent = "I couldn't find any products matching your criteria. Try adjusting your search or budget."
      }

      const assistantMessage: Message = {
        id: `msg_${Date.now() + 1}`,
        role: 'assistant',
        content: responseContent,
        products,
        recommendations
      }
      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      const errorMessage: Message = {
        id: `msg_${Date.now() + 1}`,
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.'
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleAddToCart = async (productIds: string[]) => {
    try {
      const res = await fetch('/api/agent/cart', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product_ids: productIds,
          session_id: sessionId
        })
      })
      const data = await res.json()

      setCartId(data.cart_id)
      setCartTotal(data.total)

      const cartMessage: Message = {
        id: `msg_${Date.now()}`,
        role: 'assistant',
        content: `Cart created! Here's your order summary:\n\n${data.items.map((i: any) => `${i.name} - ₹${i.price.toLocaleString()} x ${i.quantity}`).join('\n')}\n\nTotal: ₹${data.total.toLocaleString()}\n\nReady to proceed to payment?`,
        cartId: data.cart_id,
        total: data.total
      }
      setMessages(prev => [...prev, cartMessage])
    } catch (error) {
      console.error('Failed to add to cart')
    }
  }

  const handleRequestApproval = async () => {
    if (!cartId) return

    try {
      const res = await fetch('/api/agent/request-approval', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          cart_id: cartId,
          session_id: sessionId
        })
      })
      const data = await res.json()

      const approvalMessage: Message = {
        id: `msg_${Date.now()}`,
        role: 'assistant',
        content: `Payment approval requested for ₹${cartTotal.toLocaleString()}. Please approve to proceed.`,
        approvalPending: true
      }
      setMessages(prev => [...prev, approvalMessage])
    } catch (error) {
      console.error('Failed to request approval')
    }
  }

  const handleApprove = async () => {
    try {
      const approvalRes = await fetch(`/api/agent/approve/${messages.find(m => m.approvalPending)?.id || ''}`, {
        method: 'POST'
      })

      const paymentRes = await fetch('/api/payments/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ order_id: cartId })
      })
      const paymentData = await paymentRes.json()

      const paymentMessage: Message = {
        id: `msg_${Date.now()}`,
        role: 'assistant',
        content: paymentData.status === 'initiated'
          ? `Payment initiated! Order ID: ${paymentData.id}\n\nStatus: Processing...`
          : `Payment failed: ${paymentData.failure_reason || 'Unknown error'}`,
        paymentStatus: paymentData.status
      }
      setMessages(prev => [...prev, paymentMessage])
    } catch (error) {
      console.error('Failed to process payment')
    }
  }

  return (
    <div className="flex flex-col h-screen">
      <div className="bg-white border-b px-6 py-4">
        <h1 className="text-xl font-bold text-gray-900">AI Shopping Assistant</h1>
        <p className="text-sm text-gray-600">Ask me to find products for you</p>
      </div>

      <div className="flex-1 overflow-auto p-6 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🤖</div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Welcome to MerchantFlow AI</h2>
            <p className="text-gray-600 mb-6">Try asking me something like:</p>
            <div className="flex flex-wrap justify-center gap-2">
              {['Find me headphones under ₹3000', 'Show me laptop accessories', 'I need a wireless mouse'].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => setInput(suggestion)}
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

              {message.products && message.products.length > 0 && (
                <div className="mt-4 space-y-2">
                  {message.products.map((product) => (
                    <div key={product.product_id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                      <div>
                        <p className="font-medium text-gray-900">{product.name}</p>
                        <p className="text-sm text-gray-600">₹{product.price.toLocaleString()}</p>
                      </div>
                      <button
                        onClick={() => handleAddToCart([product.product_id])}
                        className="px-3 py-1 bg-primary-600 text-white text-sm rounded hover:bg-primary-700"
                      >
                        Add to Cart
                      </button>
                    </div>
                  ))}
                  {message.recommendations && message.recommendations.length > 0 && (
                    <div className="mt-3 p-3 bg-blue-50 rounded">
                      <p className="text-sm font-medium text-blue-900 mb-2">💡 Recommended Add-ons:</p>
                      {message.recommendations.map((rec) => (
                        <div key={rec.product_id} className="flex items-center justify-between py-1">
                          <div>
                            <span className="text-sm">{rec.name}</span>
                            <span className="text-sm text-gray-600 ml-2">₹{rec.price}</span>
                          </div>
                          <button
                            onClick={() => handleAddToCart([rec.product_id])}
                            className="text-xs text-primary-600 hover:underline"
                          >
                            Add
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {message.cartId && (
                <div className="mt-4 pt-4 border-t">
                  <button
                    onClick={handleRequestApproval}
                    className="w-full px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                  >
                    Proceed to Payment (₹{message.total?.toLocaleString()})
                  </button>
                </div>
              )}

              {message.approvalPending && (
                <div className="mt-4 pt-4 border-t">
                  <div className="bg-yellow-50 p-3 rounded mb-3">
                    <p className="text-sm text-yellow-800 font-medium">⚠️ Approval Required</p>
                    <p className="text-xs text-yellow-700 mt-1">
                      This payment requires your explicit approval before processing.
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={handleApprove}
                      className="flex-1 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                    >
                      ✓ Approve Payment
                    </button>
                    <button
                      onClick={() => setMessages(prev => prev.filter(m => !m.approvalPending))}
                      className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}

              {message.paymentStatus && (
                <div className={`mt-3 p-3 rounded ${
                  message.paymentStatus === 'initiated' ? 'bg-blue-50' : 'bg-red-50'
                }`}>
                  <p className={`text-sm font-medium ${
                    message.paymentStatus === 'initiated' ? 'text-blue-800' : 'text-red-800'
                  }`}>
                    {message.paymentStatus === 'initiated' ? '✅ Payment Processing' : '❌ Payment Failed'}
                  </p>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border rounded-lg px-4 py-3">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="border-t bg-white p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask me to find products..."
            className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}
