'use client'

import { useState, useRef, useEffect, useCallback } from 'react'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  products?: Product[]
  cart?: CartInfo
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
  quick_actions: QuickAction[]
}

const WELCOME_MESSAGE: Message = {
  id: 'welcome',
  role: 'assistant',
  content: "Hi! I'm your Commerce Assistant. I can help you find products, compare prices, check availability, and manage your cart.",
  quickActions: [
    { label: '🔥 Best Sellers', message: 'Show me best sellers' },
    { label: '🔍 Find Products', message: 'Show me popular products' },
    { label: '🏷️ Deals', message: 'Show me deals and discounts' },
    { label: '🛒 Show Cart', message: 'Show my cart' },
    { label: '📦 Track Order', message: 'Track my order' },
    { label: '❓ Help', message: 'Help' },
  ],
  timestamp: new Date(),
}

const FALLBACK_IMAGE = 'data:image/svg+xml,' + encodeURIComponent(
  '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200"><rect fill="#1e1b4b" width="200" height="200"/><text fill="#6366f1" font-family="Arial,sans-serif" font-size="14" text-anchor="middle" x="100" y="95">📦</text><text fill="#818cf8" font-family="Arial,sans-serif" font-size="11" text-anchor="middle" x="100" y="115">Product</text></svg>'
)

export default function CommerceChat() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([WELCOME_MESSAGE])
  const [input, setInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [minimized, setMinimized] = useState(false)
  const [cartCount, setCartCount] = useState(0)
  const [addingProductId, setAddingProductId] = useState<string | null>(null)
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
  }, [sessionId])

  const fetchCartCount = async () => {
    try {
      const res = await fetch(`/api/carts/session/${sessionId}`)
      if (res.ok) {
        const data = await res.json()
        setCartCount(data.item_count || 0)
      }
    } catch (e) {
      // Silently fail
    }
  }

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (isOpen && !minimized) {
      inputRef.current?.focus()
    }
  }, [isOpen, minimized])

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

      // Show success message in chat
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
    <>
      {/* Floating Button */}
      {!isOpen && (
        <button
          onClick={() => { setIsOpen(true); setMinimized(false) }}
          className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 text-white shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-200 flex items-center justify-center group"
          aria-label="Open Commerce Assistant"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          <span className="absolute -top-1 -right-1 w-3 h-3 bg-emerald-400 rounded-full border-2 border-white"></span>
          {cartCount > 0 && (
            <span className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center border-2 border-white">
              {cartCount}
            </span>
          )}
        </button>
      )}

      {/* Chat Panel */}
      {isOpen && (
        <div className={`fixed z-50 ${minimized ? 'bottom-6 right-6' : 'bottom-0 right-0 sm:bottom-6 sm:right-6 sm:w-[420px] sm:h-[620px] w-full h-full sm:rounded-2xl'} bg-white border border-slate-200 shadow-2xl flex flex-col overflow-hidden transition-all duration-300`}>
          {/* Header */}
          <div className="bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between flex-shrink-0">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Commerce Assistant</h3>
                <p className="text-[10px] text-slate-500">How can I help you shop today?</p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              {cartCount > 0 && (
                <a href="/cart" className="flex items-center gap-1 px-2 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 hover:text-slate-900 transition-colors text-[11px]">
                  🛒 <span className="font-medium">{cartCount}</span>
                </a>
              )}
              <button onClick={clearChat} className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500 hover:text-slate-900 transition-colors" title="Clear chat">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
              <button onClick={() => setMinimized(!minimized)} className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500 hover:text-slate-900 transition-colors" title={minimized ? 'Expand' : 'Minimize'}>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  {minimized ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                  )}
                </svg>
              </button>
              <button onClick={() => { setIsOpen(false); setMinimized(false) }} className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500 hover:text-slate-900 transition-colors" title="Close">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Messages */}
          {!minimized && (
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map(msg => (
                <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[90%] rounded-xl px-4 py-2.5 ${
                    msg.role === 'user'
                      ? 'bg-primary-600 text-white'
                      : 'bg-white border border-slate-200 text-slate-800'
                  }`}>
                    <div className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</div>

                    {/* Product Cards */}
                    {msg.products && msg.products.length > 0 && (
                      <div className="mt-3 overflow-x-auto">
                        <div className="flex gap-2 pb-2" style={{ minWidth: 'max-content' }}>
                          {msg.products.slice(0, 5).map(p => (
                            <div key={p.product_id} className="w-[200px] flex-shrink-0 bg-white rounded-lg border border-slate-200 overflow-hidden shadow-sm">
                              {/* Product Image */}
                              <div className="relative w-full h-[120px] bg-slate-100 overflow-hidden">
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
                                  <span className="absolute top-1.5 left-1.5 text-[9px] px-1.5 py-0.5 bg-amber-500/90 text-white rounded font-medium">
                                    🔥 Bestseller
                                  </span>
                                )}
                                {hasDiscount(p) && (
                                  <span className="absolute top-1.5 right-1.5 text-[9px] px-1.5 py-0.5 bg-red-500/90 text-white rounded font-medium">
                                    -{getDiscountPercent(p)}%
                                  </span>
                                )}
                              </div>
                              {/* Product Info */}
                              <div className="p-2.5">
                                <p className="text-xs font-medium text-slate-900 truncate leading-tight">{p.name}</p>
                                {p.brand && (
                                  <p className="text-[10px] text-slate-500 mt-0.5">{p.brand}</p>
                                )}
                                <div className="flex items-center gap-2 mt-1.5">
                                  <span className="text-sm font-bold text-slate-900">₹{p.price.toLocaleString()}</span>
                                  {hasDiscount(p) && (
                                    <span className="text-[10px] text-slate-400 line-through">₹{p.previous_price!.toLocaleString()}</span>
                                  )}
                                </div>
                                <div className="flex items-center gap-2 mt-1">
                                  {p.rating ? (
                                    <span className="text-[10px] text-amber-500">★ {p.rating}</span>
                                  ) : null}
                                  <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                                    p.stock > 10 ? 'bg-emerald-50 text-emerald-700' :
                                    p.stock > 0 ? 'bg-amber-50 text-amber-700' :
                                    'bg-red-50 text-red-700'
                                  }`}>
                                    {p.stock > 0 ? (p.stock <= 10 ? `Only ${p.stock} left` : 'In Stock') : 'Out of stock'}
                                  </span>
                                </div>
                                {/* Action Buttons */}
                                {p.stock > 0 && (
                                  <div className="mt-2.5 flex gap-1.5">
                                    <a
                                      href={`/product?id=${p.product_id}`}
                                      className="flex-1 text-center text-[10px] px-2 py-1.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 rounded transition-colors"
                                    >
                                      View
                                    </a>
                                    <button
                                      onClick={() => handleAddToCart(p.product_id)}
                                      disabled={addingProductId === p.product_id}
                                      className="flex-1 text-[10px] px-2 py-1.5 bg-primary-600 hover:bg-primary-500 disabled:bg-primary-800 text-white rounded transition-colors"
                                    >
                                      {addingProductId === p.product_id ? 'Adding...' : '+ Add'}
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
                      <div className="mt-3 p-3 bg-slate-50 rounded-lg border border-slate-200">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-slate-900">🛒 Cart</span>
                          <span className="text-sm font-bold text-slate-900">₹{msg.cart.total.toLocaleString()}</span>
                        </div>
                        <p className="text-xs text-slate-500 mb-2">{msg.cart.item_count} item(s)</p>
                        {msg.cart.items && msg.cart.items.length > 0 && (
                          <div className="space-y-1 mb-2">
                            {msg.cart.items.map((item, i) => (
                              <div key={i} className="flex justify-between text-[11px] text-slate-600">
                                <span className="truncate mr-2">{item.name} × {item.quantity}</span>
                                <span className="flex-shrink-0">₹{item.subtotal.toLocaleString()}</span>
                              </div>
                            ))}
                          </div>
                        )}
                        <a href="/cart" className="block text-center text-[11px] px-3 py-1.5 bg-primary-600 hover:bg-primary-500 text-white rounded transition-colors">
                          View Cart & Checkout →
                        </a>
                      </div>
                    )}

                    {/* Quick Actions */}
                    {msg.quickActions && msg.quickActions.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-1.5">
                        {msg.quickActions.map((qa, i) => (
                          <button
                            key={i}
                            onClick={() => handleSend(qa.message)}
                            className="text-[11px] px-2.5 py-1.5 bg-white hover:bg-slate-50 border border-slate-200 hover:border-primary-300 text-slate-700 hover:text-slate-900 rounded-lg transition-colors"
                          >
                            {qa.label}
                          </button>
                        ))}
                      </div>
                    )}

                    <div className="text-[9px] text-slate-400 mt-1.5 text-right">{formatTime(msg.timestamp)}</div>
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
          )}

          {/* Input */}
          {!minimized && (
            <div className="border-t border-slate-200 bg-white p-3 flex-shrink-0">
              <div className="flex gap-2">
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
                  placeholder="Ask about products, prices, orders or your cart..."
                  className="flex-1 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
                  disabled={chatLoading}
                />
                <button
                  onClick={() => handleSend()}
                  disabled={chatLoading || !input.trim()}
                  className="px-4 py-2 bg-primary-600 hover:bg-primary-500 disabled:bg-slate-300 disabled:text-slate-500 text-white rounded-lg text-sm font-medium transition-colors"
                >
                  {chatLoading ? '...' : 'Send'}
                </button>
              </div>
              <p className="text-[9px] text-slate-400 text-center mt-1.5">Commerce Assistant · No AI API required</p>
            </div>
          )}
        </div>
      )}
    </>
  )
}
