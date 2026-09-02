'use client'

import { useState, useRef, useEffect } from 'react'
import { sanitizeProductName, formatPrice } from '../utils'

interface Message {
  id: string; role: 'user' | 'assistant'; content: string;
  products?: Product[]; recommendations?: Recommendation[];
  cart?: CartInfo; approval?: ApprovalInfo; paymentStatus?: string;
}

interface Product {
  product_id: string; name: string; description: string; category: string;
  price: number; currency: string; stock: number; position?: number;
}

interface Recommendation {
  product_id: string; name: string; price: number; reason: string; type: string;
}

interface CartInfo {
  cart_id: string; total: number; item_count: number; items?: any[];
}

interface ApprovalInfo {
  approval_id: string; order_id: string; status: string; total: number; message: string;
}

interface ChatResponse {
  message: string; products: Product[]; recommendations: Recommendation[];
  cart: CartInfo | null; approval: ApprovalInfo | null; payment: any; tool_calls: any[];
}

const SUGGESTIONS = [
  "Find wireless headphones",
  "I need a phone under ₹30,000",
  "Show me laptops for programming",
  "Find accessories for my phone",
  "What's on sale today?",
  "I want something with a good camera",
  "Find the best deals under ₹5,000",
  "Show me trending products",
  "I need a gift for someone",
  "Compare wireless earbuds",
]

export default function BuyerPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId] = useState(() => {
    if (typeof window !== 'undefined') {
      let sid = localStorage.getItem('session_id')
      if (!sid) { sid = `sess_${Date.now()}`; localStorage.setItem('session_id', sid) }
      return sid
    }
    return `sess_${Date.now()}`
  })
  const [pendingApproval, setPendingApproval] = useState<ApprovalInfo | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async (text?: string) => {
    const messageText = (text || input).trim()
    if (!messageText || loading) return
    setMessages(prev => [...prev, { id: `u_${Date.now()}`, role: 'user', content: messageText }])
    setInput('')
    setLoading(true)
    try {
      const res = await fetch('/api/agent/chat', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: messageText, session_id: sessionId }),
      })
      if (!res.ok) throw new Error('Chat request failed')
      const data: ChatResponse = await res.json()
      setMessages(prev => [...prev, {
        id: `a_${Date.now()}`, role: 'assistant', content: data.message,
        products: data.products?.length ? data.products : undefined,
        recommendations: data.recommendations?.length ? data.recommendations : undefined,
        cart: data.cart || undefined, approval: data.approval || undefined,
      }])
      if (data.approval) setPendingApproval(data.approval)
    } catch (e: any) {
      setMessages(prev => [...prev, {
        id: `e_${Date.now()}`, role: 'assistant',
        content: `⚠️ Error: ${e.message || 'Unknown error'}. The chat service may be temporarily unavailable.`,
      }])
    } finally { setLoading(false) }
  }

  const handleAddProduct = async (productId: string, position?: number) => {
    setLoading(true)
    try {
      const msg = productId
        ? `Add product ${productId} to my cart`
        : `Add the ${position === 1 ? 'first' : position === 2 ? 'second' : `${position}th`} product to my cart`
      const res = await fetch('/api/agent/chat', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, session_id: sessionId }),
      })
      const data: ChatResponse = await res.json()
      setMessages(prev => [...prev, {
        id: `a_${Date.now()}`, role: 'assistant', content: data.message,
        cart: data.cart || undefined, approval: data.approval || undefined,
        recommendations: data.recommendations?.length ? data.recommendations : undefined,
      }])
      if (data.approval) setPendingApproval(data.approval)
    } catch (e) {
      setMessages(prev => [...prev, { id: `e_${Date.now()}`, role: 'assistant', content: 'Failed to add product. Try again.' }])
    } finally { setLoading(false) }
  }

  const handleApprovePayment = async () => {
    if (!pendingApproval) return
    setLoading(true)
    try {
      await fetch(`/api/approvals/${pendingApproval.approval_id}/approve`, { method: 'POST' })
      const payRes = await fetch('/api/payments/', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ order_id: pendingApproval.order_id }),
      })
      const payData = await payRes.json()
      setMessages(prev => [...prev, {
        id: `p_${Date.now()}`, role: 'assistant',
        content: payData.status === 'initiated'
          ? `✅ Payment initiated!\nOrder: ${payData.order_id}\nRazorpay: ${payData.razorpay_order_id}\nCheck Payments tab for status.`
          : `❌ Payment failed: ${payData.failure_reason || 'Unknown error'}`,
        paymentStatus: payData.status,
      }])
      setPendingApproval(null)
    } catch (e: any) {
      setMessages(prev => [...prev, { id: `e_${Date.now()}`, role: 'assistant', content: `Payment error: ${e.message}` }])
    } finally { setLoading(false) }
  }

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="bg-dark-800 border-b border-dark-700 px-6 py-3 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-white flex items-center gap-2">
              <span className="text-purple-400">🛒</span> Commerce Assistant
            </h1>
            <p className="text-xs text-dark-400">Online shopping help</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="badge-success">ONLINE</span>
            <span className="badge-info text-[10px]">Session active</span>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-auto p-4 lg:p-6 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-12 max-w-lg mx-auto">
            <div className="w-20 h-20 bg-gradient-to-br from-primary-500 to-primary-700 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <span className="text-4xl">🛒</span>
            </div>              <h2 className="text-xl font-bold text-white mb-2">Commerce Assistant</h2>
            <p className="text-dark-400 text-sm mb-6">I can help you find products, compare options, and place orders. Just tell me what you're looking for!</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {SUGGESTIONS.map(s => (
                <button key={s} onClick={() => handleSend(s)}
                  className="text-left px-3 py-2.5 bg-dark-800 border border-dark-600 rounded-lg text-sm text-dark-200 hover:border-primary-500/50 hover:text-white transition-colors">
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map(msg => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-2xl rounded-xl px-4 py-3 ${
              msg.role === 'user' ? 'bg-primary-600 text-white' : 'bg-dark-800 border border-dark-700 text-dark-100'
            }`}>
              <div className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</div>

              {msg.products && msg.products.length > 0 && (
                <div className="mt-3 space-y-2">
                  {msg.products.map(p => (
                    <div key={p.product_id} className="flex items-center gap-3 p-3 bg-dark-700/50 rounded-lg border border-dark-600">
                      <div className="w-10 h-10 bg-primary-600/20 rounded-lg flex items-center justify-center flex-shrink-0">
                        <span className="text-xs font-bold text-primary-400">#{p.position}</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm text-white truncate">{sanitizeProductName(p.name)}</p>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-xs font-bold text-primary-400">₹{p.price.toLocaleString()}</span>
                          <span className="text-[10px] text-dark-400">{p.category}</span>
                          <span className={`text-[10px] px-1 py-0.5 rounded ${p.stock > 10 ? 'bg-emerald-500/10 text-emerald-400' : p.stock > 0 ? 'bg-amber-500/10 text-amber-400' : 'bg-red-500/10 text-red-400'}`}>
                            {p.stock > 0 ? `${p.stock} stock` : 'Out'}
                          </span>
                        </div>
                      </div>
                      {p.stock > 0 && (
                        <button onClick={() => handleAddProduct(p.product_id, p.position)}
                          className="btn-primary text-xs px-3 py-1.5 flex-shrink-0">+ Cart</button>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {msg.recommendations && msg.recommendations.length > 0 && (
                <div className="mt-3 p-3 bg-primary-500/5 border border-primary-500/10 rounded-lg">
                  <p className="text-xs font-medium text-primary-300 mb-2">💡 Recommended Add-ons</p>
                  {msg.recommendations.map(r => (
                    <div key={r.product_id} className="flex items-center justify-between py-1.5">
                      <div>
                        <span className="text-sm text-dark-100">{sanitizeProductName(r.name)}</span>
                        <span className="text-xs text-dark-400 ml-2">₹{r.price.toLocaleString()}</span>
                        {r.reason && <p className="text-[10px] text-primary-400/80">{r.reason}</p>}
                      </div>
                      <button onClick={() => handleAddProduct(r.product_id)} className="text-xs text-primary-400 hover:text-primary-300 font-medium">+ Add</button>
                    </div>
                  ))}
                </div>
              )}

              {msg.cart && (
                <div className="mt-3 p-3 bg-dark-700/50 rounded-lg border border-dark-600">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-white">🛒 Cart</span>
                    <span className="text-lg font-bold text-primary-400">₹{msg.cart.total.toLocaleString()}</span>
                  </div>
                  <p className="text-xs text-dark-400">{msg.cart.item_count} items</p>
                  <a href="/cart" className="btn-primary w-full mt-2 text-xs py-2 block text-center">View Cart & Checkout →</a>
                </div>
              )}

              {msg.approval && (
                <div className="mt-3 p-3 bg-amber-500/5 border border-amber-500/20 rounded-lg">
                  <p className="text-sm font-medium text-amber-300 mb-1">⚠️ Approval Required</p>
                  <p className="text-xs text-dark-300 mb-3">Total: ₹{msg.approval.total.toLocaleString()}</p>
                  <div className="flex gap-2">
                    <button onClick={handleApprovePayment} className="btn-success flex-1 text-xs py-2">✓ Approve</button>
                    <button onClick={() => setPendingApproval(null)} className="btn-secondary flex-1 text-xs py-2">Cancel</button>
                  </div>
                </div>
              )}

              {msg.paymentStatus && (
                <div className={`mt-3 p-2 rounded text-sm ${msg.paymentStatus === 'initiated' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                  {msg.paymentStatus === 'initiated' ? '✅ Payment Processing' : '❌ Payment Failed'}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-dark-800 border border-dark-700 rounded-xl px-4 py-3">
              <div className="flex items-center gap-2">
                <span className="text-sm text-dark-400">Thinking</span>
                <div className="flex gap-1">
                  {[0, 1, 2].map(i => (
                    <div key={i} className="w-1.5 h-1.5 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: `${i * 0.1}s` }}></div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-dark-700 bg-dark-800 p-4 flex-shrink-0">
        <div className="flex gap-2 max-w-3xl mx-auto">
          <input type="text" value={input} onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder="Ask about products, inventory, pricing, or start shopping..."
            className="input flex-1" disabled={loading} />
          <button onClick={() => handleSend()} disabled={loading || !input.trim()}
            className="btn-primary px-6">{loading ? '...' : 'Send'}</button>
        </div>
        <p className="text-[10px] text-dark-500 text-center mt-2">Commerce Assistant · Online Shopping Help</p>
      </div>
    </div>
  )
}
