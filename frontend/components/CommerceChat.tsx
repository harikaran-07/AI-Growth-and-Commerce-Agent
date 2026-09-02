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
  price: number
  currency: string
  stock: number
  position?: number
  rating?: number
  discount?: number
  brand?: string
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
    { label: 'Find Products', message: 'Show me popular products' },
    { label: "Today's Deals", message: 'Show me deals and discounts' },
    { label: 'Show Cart', message: 'Show my cart' },
    { label: 'Track Order', message: 'Track my order' },
    { label: 'Help', message: 'Help' },
  ],
  timestamp: new Date(),
}

export default function CommerceChat() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([WELCOME_MESSAGE])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [minimized, setMinimized] = useState(false)
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
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (isOpen && !minimized) {
      inputRef.current?.focus()
    }
  }, [isOpen, minimized])

  const handleSend = useCallback(async (text?: string) => {
    const messageText = (text || input).trim()
    if (!messageText || loading) return

    const userMsg: Message = {
      id: `u_${Date.now()}`,
      role: 'user',
      content: messageText,
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

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
      setLoading(false)
    }
  }, [input, loading, sessionId])

  const handleAddToCart = useCallback(async (productId: string) => {
    setLoading(true)
    try {
      const res = await fetch('/api/agent/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: `Add product ${productId} to my cart`, session_id: sessionId }),
      })
      const data: ChatResponse = await res.json()
      setMessages(prev => [...prev, {
        id: `a_${Date.now()}`,
        role: 'assistant',
        content: data.message,
        cart: data.cart || undefined,
        timestamp: new Date(),
      }])
    } catch {
      setMessages(prev => [...prev, {
        id: `e_${Date.now()}`,
        role: 'assistant',
        content: "Couldn't add to cart. Please try again.",
        timestamp: new Date(),
      }])
    } finally {
      setLoading(false)
    }
  }, [sessionId])

  const clearChat = () => {
    setMessages([WELCOME_MESSAGE])
  }

  const formatTime = (d: Date) => d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

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
        </button>
      )}

      {/* Chat Panel */}
      {isOpen && (
        <div className={`fixed z-50 ${minimized ? 'bottom-6 right-6' : 'bottom-0 right-0 sm:bottom-6 sm:right-6 sm:w-[400px] sm:h-[600px] w-full h-full sm:rounded-2xl'} bg-dark-900 border border-dark-600 shadow-2xl flex flex-col overflow-hidden transition-all duration-300`}>
          {/* Header */}
          <div className="bg-dark-800 border-b border-dark-600 px-4 py-3 flex items-center justify-between flex-shrink-0">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">Commerce Assistant</h3>
                <p className="text-[10px] text-dark-400">How can I help you shop today?</p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button onClick={clearChat} className="p-1.5 rounded-lg hover:bg-dark-700 text-dark-400 hover:text-white transition-colors" title="Clear chat">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
              <button onClick={() => setMinimized(!minimized)} className="p-1.5 rounded-lg hover:bg-dark-700 text-dark-400 hover:text-white transition-colors" title={minimized ? 'Expand' : 'Minimize'}>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  {minimized ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                  )}
                </svg>
              </button>
              <button onClick={() => { setIsOpen(false); setMinimized(false) }} className="p-1.5 rounded-lg hover:bg-dark-700 text-dark-400 hover:text-white transition-colors" title="Close">
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
                  <div className={`max-w-[85%] rounded-xl px-4 py-2.5 ${
                    msg.role === 'user'
                      ? 'bg-primary-600 text-white'
                      : 'bg-dark-800 border border-dark-700 text-dark-100'
                  }`}>
                    <div className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</div>

                    {/* Product Cards */}
                    {msg.products && msg.products.length > 0 && (
                      <div className="mt-3 space-y-2">
                        {msg.products.slice(0, 5).map(p => (
                          <div key={p.product_id} className="bg-dark-700/50 rounded-lg p-3 border border-dark-600">
                            <div className="flex items-start justify-between gap-2">
                              <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium text-white truncate">{p.name}</p>
                                <div className="flex items-center gap-2 mt-1">
                                  <span className="text-xs font-bold text-primary-400">₹{p.price.toLocaleString()}</span>
                                  {p.brand && <span className="text-[10px] text-dark-400">{p.brand}</span>}
                                  <span className="text-[10px] text-dark-500">{p.category}</span>
                                </div>
                                <div className="flex items-center gap-2 mt-1">
                                  {p.rating && (
                                    <span className="text-[10px] text-amber-400">★ {p.rating}</span>
                                  )}
                                  <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                                    p.stock > 10 ? 'bg-emerald-500/10 text-emerald-400' :
                                    p.stock > 0 ? 'bg-amber-500/10 text-amber-400' :
                                    'bg-red-500/10 text-red-400'
                                  }`}>
                                    {p.stock > 0 ? `${p.stock} in stock` : 'Out of stock'}
                                  </span>
                                </div>
                              </div>
                            </div>
                            {p.stock > 0 && (
                              <div className="mt-2 flex gap-2">
                                <a href={`/product?id=${p.product_id}`} className="text-[10px] px-2.5 py-1 bg-dark-600 hover:bg-dark-500 text-dark-200 rounded transition-colors">
                                  View Product
                                </a>
                                <button
                                  onClick={() => handleAddToCart(p.product_id)}
                                  className="text-[10px] px-2.5 py-1 bg-primary-600 hover:bg-primary-500 text-white rounded transition-colors"
                                >
                                  + Add to Cart
                                </button>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Cart Info */}
                    {msg.cart && (
                      <div className="mt-3 p-3 bg-dark-700/50 rounded-lg border border-dark-600">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-white">🛒 Cart</span>
                          <span className="text-sm font-bold text-primary-400">₹{msg.cart.total.toLocaleString()}</span>
                        </div>
                        <p className="text-xs text-dark-400 mb-2">{msg.cart.item_count} item(s)</p>
                        {msg.cart.items && msg.cart.items.length > 0 && (
                          <div className="space-y-1 mb-2">
                            {msg.cart.items.map((item, i) => (
                              <div key={i} className="flex justify-between text-[11px] text-dark-300">
                                <span>{item.name} × {item.quantity}</span>
                                <span>₹{item.subtotal.toLocaleString()}</span>
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
                            className="text-[11px] px-2.5 py-1.5 bg-dark-700 hover:bg-dark-600 border border-dark-600 hover:border-primary-500/50 text-dark-200 hover:text-white rounded-lg transition-colors"
                          >
                            {qa.label}
                          </button>
                        ))}
                      </div>
                    )}

                    <div className="text-[9px] text-dark-500 mt-1.5 text-right">{formatTime(msg.timestamp)}</div>
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
            <div className="border-t border-dark-700 bg-dark-800 p-3 flex-shrink-0">
              <div className="flex gap-2">
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
                  placeholder="Ask about products, prices, orders or your cart..."
                  className="flex-1 bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-sm text-dark-100 placeholder-dark-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
                  disabled={loading}
                />
                <button
                  onClick={() => handleSend()}
                  disabled={loading || !input.trim()}
                  className="px-4 py-2 bg-primary-600 hover:bg-primary-500 disabled:bg-dark-600 disabled:text-dark-400 text-white rounded-lg text-sm font-medium transition-colors"
                >
                  {loading ? '...' : 'Send'}
                </button>
              </div>
              <p className="text-[9px] text-dark-500 text-center mt-1.5">Commerce Assistant · No AI API required</p>
            </div>
          )}
        </div>
      )}
    </>
  )
}
