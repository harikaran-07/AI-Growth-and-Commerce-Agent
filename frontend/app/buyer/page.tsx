'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { sanitizeProductName } from '../utils'

interface PaymentInfo {
  order_id: string
  payment_id: string
  razorpay_order_id: string
  amount: number
  currency: string
  key_id?: string
  subtotal: number
  discount: number
  tax: number
  shipping: number
  total: number
  items?: { product_id: string; product_name: string; quantity: number; price: number; subtotal: number }[]
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  products?: Product[]
  cart?: CartInfo
  payment?: PaymentInfo
  quickActions?: QuickAction[]
  timestamp: Date
}

interface Product {
  product_id: string
  name: string
  description: string
  category: string
  subcategory?: string
  price: number
  previous_price?: number
  currency: string
  stock: number
  position?: number
  rating?: number
  discount?: number
  brand?: string
  image_url?: string
  sales?: number
  bestseller_score?: number
  reason?: string
  type?: string
}

interface CartInfo {
  cart_id: string
  total: number
  item_count: number
  items?: { name: string; quantity: number; price: number; subtotal: number }[]
}

interface QuickAction {
  label: string
  message: string
}

interface ChatResponse {
  message: string
  products: Product[]
  cart: CartInfo | null
  payment: PaymentInfo | null
  quick_actions: QuickAction[]
}

const WELCOME_MESSAGE: Message = {
  id: 'welcome',
  role: 'assistant',
  content: "Hi! I'm your **Commerce Assistant** 👋 I can find & compare real products, recommend accessories, manage your shared cart, and guide you through Razorpay TEST MODE checkout — or just answer questions. Try one of these, or ask me anything in plain language.",
  quickActions: [
    { label: '🔍 Find products', message: 'Show me laptops under 60000' },
    { label: '🔥 Best sellers', message: 'Show me best sellers' },
    { label: '🛒 My cart', message: "What's in my cart?" },
    { label: '💳 How to pay?', message: 'How can I pay?' },
    { label: '📦 Track order', message: 'Where is my order?' },
    { label: '❓ Help', message: 'What can you do?' },
  ],
  timestamp: new Date(),
}

const FALLBACK_IMAGE = 'data:image/svg+xml,' + encodeURIComponent(
  '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200"><rect fill="#1e1b4b" width="200" height="200"/><text fill="#6366f1" font-family="Arial,sans-serif" font-size="14" text-anchor="middle" x="100" y="95">📦</text><text fill="#818cf8" font-family="Arial,sans-serif" font-size="11" text-anchor="middle" x="100" y="115">Product</text></svg>'
)

export default function BuyerPage() {
  const [messages, setMessages] = useState<Message[]>([WELCOME_MESSAGE])
  const [input, setInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [cartCount, setCartCount] = useState(0)
  const [addingProductId, setAddingProductId] = useState<string | null>(null)
  const [payingOrder, setPayingOrder] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const sessionId = typeof window !== 'undefined'
    ? localStorage.getItem('session_id') || (() => {
        const sid = `sess_${Date.now()}`
        localStorage.setItem('session_id', sid)
        return sid
      })()
    : 'default'

  useEffect(() => {
    fetchCartCount()
    inputRef.current?.focus()
  }, [sessionId])

  const fetchCartCount = async () => {
    try {
      const res = await fetch(`/api/carts/session/${sessionId}`)
      if (res.ok) {
        const data = await res.json()
        setCartCount(data.item_count || 0)
      }
    } catch (e) {}
  }

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = useCallback(async (text?: string) => {
    const messageText = (text || input).trim()
    if (!messageText || chatLoading) return

    const userMsg: Message = {
      id: `u_${Date.now()}`,
      role: 'user',
      content: messageText,
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setChatLoading(true)

    try {
      const res = await fetch('/api/agent/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: messageText, session_id: sessionId }),
      })
      if (!res.ok) throw new Error('Chat request failed')
      const data: ChatResponse = await res.json()

      const assistantMsg: Message = {
        id: `a_${Date.now()}`,
        role: 'assistant',
        content: data.message,
        products: data.products?.length ? data.products : undefined,
        cart: data.cart || undefined,
        payment: data.payment || undefined,
        quickActions: data.quick_actions?.length ? data.quick_actions : undefined,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, assistantMsg])
    } catch {
      setMessages(prev => [...prev, {
        id: `e_${Date.now()}`,
        role: 'assistant',
        content: "Sorry, I couldn't process that right now. Please try again.",
        timestamp: new Date(),
      }])
    } finally {
      setChatLoading(false)
    }
  }, [input, chatLoading, sessionId])

  const handleAddToCart = useCallback(async (productId: string) => {
    setAddingProductId(productId)
    try {
      const res = await fetch(`/api/carts/session/${sessionId}/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: productId, quantity: 1 }),
      })

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}))
        const errorMsg = errorData.detail || errorData.error || 'Failed to add to cart'
        throw new Error(errorMsg)
      }

      const cartData = await res.json()
      setCartCount(cartData.item_count || 0)

      setMessages(prev => [...prev, {
        id: `a_${Date.now()}`,
        role: 'assistant',
        content: `✅ Added to your cart! (${cartData.item_count} item${cartData.item_count !== 1 ? 's' : ''} · ₹${cartData.total.toLocaleString()})`,
        cart: {
          cart_id: cartData.id,
          total: cartData.total,
          item_count: cartData.item_count,
          items: cartData.items?.map((i: any) => ({
            name: i.product_name,
            quantity: i.quantity,
            price: i.price_at_time,
            subtotal: i.subtotal,
          })),
        },
        quickActions: [
          { label: '🛒 View Cart', message: 'Show my cart' },
          { label: '🔍 Continue Shopping', message: 'Show me popular products' },
        ],
        timestamp: new Date(),
      }])
    } catch (err: any) {
      setMessages(prev => [...prev, {
        id: `e_${Date.now()}`,
        role: 'assistant',
        content: err.message || "Sorry, I couldn't add this product to your cart. Please try again.",
        timestamp: new Date(),
      }])
    } finally {
      setAddingProductId(null)
    }
  }, [sessionId])

  const payWithRazorpay = useCallback(async (msg: Message) => {
    const payment = msg.payment
    if (!payment) return
    setPayingOrder(payment.order_id)

    const paymentFailed = (text: string) => {
      setMessages(prev => [...prev, {
        id: `payf_${Date.now()}`,
        role: 'assistant',
        content: text,
        timestamp: new Date(),
      }])
    }
    const paymentSuccess = () => {
      setMessages(prev => [...prev, {
        id: `pays_${Date.now()}`,
        role: 'assistant',
        content: `✅ Payment successful! Order #${payment.order_id.slice(0, 8).toUpperCase()} has been paid (₹${payment.total.toLocaleString()}). Thank you for shopping with us!`,
        timestamp: new Date(),
      }])
      fetchCartCount()
    }

    try {
      if (payment.key_id) {
        // Real Razorpay TEST MODE checkout
        const options = {
          key: payment.key_id,
          amount: payment.amount,
          currency: payment.currency,
          name: 'AI Growth & Commerce',
          description: `Order #${payment.order_id.slice(0, 8)}`,
          order_id: payment.razorpay_order_id,
          handler: async (response: any) => {
            try {
              const verifyRes = await fetch('/api/payments/verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  razorpay_order_id: response.razorpay_order_id,
                  razorpay_payment_id: response.razorpay_payment_id,
                  razorpay_signature: response.razorpay_signature,
                  order_id: payment.order_id,
                }),
              })
              const verifyData = await verifyRes.json()
              if (verifyRes.ok) {
                paymentSuccess()
              } else {
                paymentFailed(`❌ Payment was not completed. Your order has NOT been marked as paid. ${verifyData?.detail || 'Please try again.'}`)
              }
            } catch (e) {
              paymentFailed('⚠️ Payment verification error. Please check your payment status on the Payments page.')
            }
            setPayingOrder(null)
          },
          theme: { color: '#7c3aed' },
          modal: {
            ondismiss: () => { setPayingOrder(null) },
          },
        }
        const rzp = new window.Razorpay(options)
        rzp.on('payment.failed', () => {
          paymentFailed('❌ Payment failed. Your order has NOT been marked as paid. You can retry payment.')
          setPayingOrder(null)
        })
        rzp.open()
      } else {
        // Demo mode (no Razorpay keys configured) - simulate success
        setTimeout(async () => {
          try {
            const demoRes = await fetch(`/api/payments/demo-success/${payment.order_id}`, { method: 'POST' })
            if (demoRes.ok) {
              paymentSuccess()
            } else {
              paymentFailed('❌ Payment was not completed. Your order has NOT been marked as paid. Please try again.')
            }
          } catch (e) {
            paymentFailed('⚠️ Demo payment simulation failed. Please try again.')
          }
          setPayingOrder(null)
        }, 1500)
      }
    } catch (e) {
      paymentFailed('⚠️ Failed to initialize payment. Please try again.')
      setPayingOrder(null)
    }
  }, [sessionId])

  // Load Razorpay checkout script
  useEffect(() => {
    const script = document.createElement('script')
    script.src = 'https://checkout.razorpay.com/v1/checkout.js'
    script.async = true
    document.body.appendChild(script)
    return () => { document.body.removeChild(script) }
  }, [])

  const clearChat = () => {
    setMessages([WELCOME_MESSAGE])
  }

  const formatTime = (d: Date) => d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

  const isBestseller = (p: Product): boolean => {
    return (p.sales || 0) >= 50 || (p.rating || 0) >= 4.5
  }

  const hasDiscount = (p: Product): boolean => {
    return !!(p.previous_price && p.previous_price > p.price)
  }

  const getDiscountPercent = (p: Product): number => {
    if (!p.previous_price || p.previous_price <= p.price) return 0
    return Math.round(((p.previous_price - p.price) / p.previous_price) * 100)
  }

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-6 py-3 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <div>
              <h1 className="text-sm font-semibold text-slate-900">Commerce Assistant</h1>
              <p className="text-[10px] text-slate-500">How can I help you shop today?</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {cartCount > 0 && (
              <a href="/cart" className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 hover:text-slate-900 transition-colors text-xs">
                🛒 <span className="font-medium">{cartCount}</span>
              </a>
            )}
            <button onClick={clearChat} className="p-2 rounded-lg hover:bg-slate-100 text-slate-500 hover:text-slate-900 transition-colors" title="Clear chat">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 lg:p-6 space-y-4">
        {messages.map(msg => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-3xl rounded-xl px-4 py-3 ${
              msg.role === 'user'
                ? 'bg-primary-600 text-white'
                : 'bg-white border border-slate-200 text-slate-800'
            }`}>
              <div className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</div>

              {/* Product Cards */}
              {msg.products && msg.products.length > 0 && (
                <div className="mt-3 overflow-x-auto">
                  <div className="flex gap-3 pb-2" style={{ minWidth: 'max-content' }}>
                    {msg.products.slice(0, 5).map(p => (
                      <div key={p.product_id} className="w-[220px] flex-shrink-0 bg-white rounded-lg border border-slate-200 overflow-hidden shadow-sm">
                        {/* Product Image */}
                        <div className="relative w-full h-[130px] bg-slate-100 overflow-hidden">
                          <img
                            src={p.image_url || FALLBACK_IMAGE}
                            alt={p.name}
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              const target = e.target as HTMLImageElement
                              target.src = FALLBACK_IMAGE
                            }}
                          />
                          {isBestseller(p) && (
                            <span className="absolute top-2 left-2 text-[10px] px-2 py-0.5 bg-amber-500/90 text-white rounded font-medium">
                              🔥 Bestseller
                            </span>
                          )}
                          {hasDiscount(p) && (
                            <span className="absolute top-2 right-2 text-[10px] px-2 py-0.5 bg-red-500/90 text-white rounded font-medium">
                              -{getDiscountPercent(p)}%
                            </span>
                          )}
                        </div>
                        {/* Product Info */}
                        <div className="p-3">
                          <p className="text-sm font-medium text-slate-900 truncate leading-tight">{sanitizeProductName(p.name)}</p>
                          {p.brand && (
                            <p className="text-[11px] text-slate-500 mt-0.5">{p.brand}</p>
                          )}
                          {p.reason && (
                            <p className="text-[10px] text-violet-600 leading-snug mt-1">💡 {p.reason}</p>
                          )}
                          <div className="flex items-center gap-2 mt-2">
                            <span className="text-base font-bold text-slate-900">₹{p.price.toLocaleString()}</span>
                            {hasDiscount(p) && (
                              <span className="text-[11px] text-slate-400 line-through">₹{p.previous_price!.toLocaleString()}</span>
                            )}
                          </div>
                          <div className="flex items-center gap-2 mt-1">
                            {p.rating ? (
                              <span className="text-[11px] text-amber-500">★ {p.rating}</span>
                            ) : null}
                            <span className={`text-[11px] px-1.5 py-0.5 rounded ${
                              p.stock > 10 ? 'bg-emerald-50 text-emerald-700' :
                              p.stock > 0 ? 'bg-amber-50 text-amber-700' :
                              'bg-red-50 text-red-700'
                            }`}>
                              {p.stock > 0 ? (p.stock <= 10 ? `Only ${p.stock} left` : 'In Stock') : 'Out of stock'}
                            </span>
                          </div>
                          {/* Action Buttons */}
                          {p.stock > 0 && (
                            <div className="mt-3 flex gap-2">
                              <a
                                href={`/product?id=${p.product_id}`}
                                className="flex-1 text-center text-[11px] px-3 py-2 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-lg transition-colors"
                              >
                                View
                              </a>
                              <button
                                onClick={() => handleAddToCart(p.product_id)}
                                disabled={addingProductId === p.product_id}
                                className="flex-1 text-[11px] px-3 py-2 bg-primary-600 hover:bg-primary-500 disabled:bg-primary-800 text-white rounded-lg transition-colors"
                              >
                                {addingProductId === p.product_id ? 'Adding...' : '+ Add to Cart'}
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Cart Info */}
              {msg.cart && (
                <div className="mt-3 p-4 bg-slate-50 rounded-lg border border-slate-200">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-slate-900">🛒 Cart</span>
                    <span className="text-sm font-bold text-slate-900">₹{msg.cart.total.toLocaleString()}</span>
                  </div>
                  <p className="text-xs text-slate-500 mb-2">{msg.cart.item_count} item(s)</p>
                  {msg.cart.items && msg.cart.items.length > 0 && (
                    <div className="space-y-1 mb-3">
                      {msg.cart.items.map((item, i) => (
                        <div key={i} className="flex justify-between text-xs text-slate-600">
                          <span className="truncate mr-2">{item.name} × {item.quantity}</span>
                          <span className="flex-shrink-0">₹{item.subtotal.toLocaleString()}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  <a href="/cart" className="block text-center text-xs px-3 py-2 bg-primary-600 hover:bg-primary-500 text-white rounded-lg transition-colors">
                    View Cart & Checkout →
                  </a>
                </div>
              )}

              {/* Payment / Checkout Info */}
              {msg.payment && (
                <div className="mt-3 p-4 bg-slate-50 rounded-lg border border-slate-200">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-slate-900">💳 Checkout</span>
                    <span className="text-sm font-bold text-slate-900">₹{msg.payment.total.toLocaleString()}</span>
                  </div>
                  <p className="text-xs text-slate-500 mb-2">Order #{msg.payment.order_id.slice(0, 8).toUpperCase()} · Razorpay TEST MODE</p>
                  {msg.payment.items && msg.payment.items.length > 0 && (
                    <div className="space-y-1 mb-2">
                      {msg.payment.items.map((item, i) => (
                        <div key={i} className="flex justify-between text-xs text-slate-600">
                          <span className="truncate mr-2">{item.product_name} × {item.quantity}</span>
                          <span className="flex-shrink-0">₹{item.subtotal.toLocaleString()}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  <div className="space-y-1 text-xs mb-3">
                    <div className="flex justify-between text-slate-500"><span>Subtotal</span><span>₹{msg.payment.subtotal.toLocaleString()}</span></div>
                    {msg.payment.discount > 0 && (
                      <div className="flex justify-between text-emerald-600"><span>Discount</span><span>-₹{msg.payment.discount.toLocaleString()}</span></div>
                    )}
                    <div className="flex justify-between text-slate-500"><span>Tax (18%)</span><span>₹{msg.payment.tax.toLocaleString()}</span></div>
                    <div className="flex justify-between text-slate-500"><span>Shipping</span><span>{msg.payment.shipping === 0 ? 'Free' : `₹${msg.payment.shipping}`}</span></div>
                    <div className="flex justify-between border-t border-slate-200 pt-1 text-slate-900 font-semibold"><span>Total</span><span>₹{msg.payment.total.toLocaleString()}</span></div>
                  </div>
                  <button
                    onClick={() => payWithRazorpay(msg)}
                    disabled={payingOrder === msg.payment.order_id}
                    className="w-full text-xs px-3 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-300 text-white rounded-lg transition-colors font-medium"
                  >
                    {payingOrder === msg.payment.order_id ? '⏳ Processing...' : '💳 Pay with Razorpay'}
                  </button>
                  <p className="text-[10px] text-slate-400 text-center mt-1.5">TEST MODE — No real money charged</p>
                </div>
              )}

              {/* Quick Actions */}
              {msg.quickActions && msg.quickActions.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {msg.quickActions.map((qa, i) => (
                    <button
                      key={i}
                      onClick={() => handleSend(qa.message)}
                      className="text-xs px-3 py-2 bg-white hover:bg-slate-50 border border-slate-200 hover:border-primary-300 text-slate-700 hover:text-slate-900 rounded-lg transition-colors"
                    >
                      {qa.label}
                    </button>
                  ))}
                </div>
              )}

              <div className="text-[10px] text-slate-400 mt-2 text-right">{formatTime(msg.timestamp)}</div>
            </div>
          </div>
        ))}

        {chatLoading && (
          <div className="flex justify-start">
            <div className="bg-white border border-slate-200 rounded-xl px-4 py-3">
              <div className="flex items-center gap-2">
                <span className="text-sm text-slate-500">Thinking</span>
                <div className="flex gap-1">
                  {[0, 1, 2].map(i => (
                    <div key={i} className="w-1.5 h-1.5 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: `${i * 0.1}s` }} />
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-slate-200 bg-white p-4 flex-shrink-0">
        <div className="flex gap-2 max-w-3xl mx-auto">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder="Ask about products, prices, orders or your cart..."
            className="flex-1 bg-slate-50 border border-slate-200 rounded-lg px-4 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
            disabled={chatLoading}
          />
          <button
            onClick={() => handleSend()}
            disabled={chatLoading || !input.trim()}
            className="px-5 py-2.5 bg-primary-600 hover:bg-primary-500 disabled:bg-slate-300 disabled:text-slate-500 text-white rounded-lg text-sm font-medium transition-colors"
          >
            {chatLoading ? '...' : 'Send'}
          </button>
        </div>
        <p className="text-[10px] text-slate-400 text-center mt-2">Commerce Assistant · No AI API required</p>
      </div>
    </div>
  )
}
