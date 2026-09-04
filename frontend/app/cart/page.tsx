'use client'

import { useEffect, useState } from 'react'
import { sanitizeProductName, formatPrice } from '../utils'

interface CartItem {
  id: string; product_id: string; product_name: string;
  quantity: number; price_at_time: number; subtotal: number;
  image_url?: string;
}

interface Cart {
  id: string; status: string; total: number; items: CartItem[]; item_count: number;
}

interface OrderInfo {
  id: string; subtotal: number; discount: number; tax: number;
  shipping: number; total: number; status: string;
}

declare global {
  interface Window { Razorpay: any }
}

export default function CartPage() {
  const [cart, setCart] = useState<Cart | null>(null)
  const [loading, setLoading] = useState(true)
  const [sessionId] = useState(() => {
    if (typeof window !== 'undefined') {
      let sid = localStorage.getItem('session_id')
      if (!sid) { sid = `sess_${Date.now()}`; localStorage.setItem('session_id', sid) }
      return sid
    }
    return `sess_${Date.now()}`
  })
  const [showCheckout, setShowCheckout] = useState(false)
  const [checkoutData, setCheckoutData] = useState({ name: '', email: '', phone: '', address: '' })
  const [processing, setProcessing] = useState(false)
  const [orderResult, setOrderResult] = useState<OrderInfo | null>(null)
  const [paymentError, setPaymentError] = useState('')
  const [step, setStep] = useState<'cart' | 'checkout' | 'payment' | 'success' | 'failed'>('cart')

  useEffect(() => { fetchCart() }, [sessionId])

  const fetchCart = async () => {
    try {
      const res = await fetch(`/api/carts/session/${sessionId}`)
      if (res.ok) { const data = await res.json(); setCart(data) }
    } catch (e) { console.error('Failed to fetch cart') }
    finally { setLoading(false) }
  }

  const updateQuantity = async (productId: string, qty: number) => {
    try {
      if (qty <= 0) {
        await fetch(`/api/carts/session/${sessionId}/item/${productId}`, { method: 'DELETE' })
      } else {
        await fetch(`/api/carts/session/${sessionId}/item/${productId}`, {
          method: 'PATCH', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ quantity: qty }),
        })
      }
      fetchCart()
    } catch (e) { console.error('Update failed') }
  }

  const removeItem = async (productId: string) => {
    try {
      await fetch(`/api/carts/session/${sessionId}/item/${productId}`, { method: 'DELETE' })
      fetchCart()
    } catch (e) { console.error('Remove failed') }
  }

  const clearCart = async () => {
    try {
      await fetch(`/api/carts/session/${sessionId}/clear`, { method: 'DELETE' })
      fetchCart()
    } catch (e) { console.error('Clear failed') }
  }

  const formatApiError = (error: any): string => {
    if (typeof error === 'string') return error
    if (error?.message) return error.message
    if (error?.detail) {
      if (typeof error.detail === 'string') return error.detail
      if (Array.isArray(error.detail)) {
        return error.detail.map((e: any) => e.msg || e.message || String(e)).join('; ')
      }
      if (typeof error.detail === 'object') return JSON.stringify(error.detail)
    }
    if (typeof error === 'object') {
      try {
        const str = JSON.stringify(error)
        if (str === '{}') return 'An unknown error occurred. Please try again.'
        return str
      } catch { return 'An unknown error occurred.' }
    }
    return 'Checkout failed. Please try again.'
  }

  const handleCheckout = async () => {
    if (!checkoutData.name || !checkoutData.name.trim()) {
      setPaymentError('Please enter your full name')
      return
    }
    if (!checkoutData.email || !checkoutData.email.includes('@')) {
      setPaymentError('Please enter a valid email address')
      return
    }
    if (!cart || cart.items.length === 0) {
      setPaymentError('Your cart is empty')
      return
    }
    setProcessing(true)
    setPaymentError('')
    try {
      const res = await fetch('/api/orders/checkout', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          customer_name: checkoutData.name.trim(),
          customer_email: checkoutData.email.trim(),
          customer_phone: checkoutData.phone.trim(),
          customer_address: checkoutData.address.trim(),
        }),
      })
      const data = await res.json()
      if (!res.ok) {
        throw new Error(formatApiError(data))
      }
      const order: OrderInfo = data
      setOrderResult(order)
      setStep('payment')
    } catch (e: any) {
      setPaymentError(formatApiError(e) || 'Checkout failed. Please try again.')
    } finally { setProcessing(false) }
  }

  const initRazorpay = () => {
    setProcessing(true)
    setPaymentError('')

    // First create a Razorpay order
    fetch('/api/payments/create-order', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ order_id: orderResult!.id }),
    })
    .then(r => r.json())
    .then(data => {
      if (data?.error) {
        setPaymentError(formatApiError(data))
        setProcessing(false)
        return
      }
      if (data.key_id) {
        // Real Razorpay
        const options = {
          key: data.key_id,
          amount: data.amount,
          currency: data.currency,
          name: 'AI Growth & Commerce',
          description: `Order #${orderResult!.id.slice(0, 8)}`,
          order_id: data.razorpay_order_id,
          handler: async (response: any) => {
            try {
              const verifyRes = await fetch('/api/payments/verify', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  razorpay_order_id: response.razorpay_order_id,
                  razorpay_payment_id: response.razorpay_payment_id,
                  razorpay_signature: response.razorpay_signature,
                  order_id: orderResult!.id,
                }),
              })
              const verifyData = await verifyRes.json()
              if (verifyRes.ok) {
                setStep('success')
                fetchCart()
              } else {
                setPaymentError(formatApiError(verifyData) || 'Payment verification failed')
                setStep('failed')
              }
            } catch (e) {
              setPaymentError('Payment verification error. Please check your payment status.')
              setStep('failed')
            }
            setProcessing(false)
          },
          prefill: { name: checkoutData.name, email: checkoutData.email, contact: checkoutData.phone },
          theme: { color: '#7c3aed' },
          modal: {
            ondismiss: () => { setProcessing(false); setPaymentError('Payment cancelled. Your cart is still available. You can retry from the payment step.') },
          },
        }
        const rzp = new window.Razorpay(options)
        rzp.on('payment.failed', () => {
          setPaymentError('Payment failed. Please try again.')
          setStep('failed')
          setProcessing(false)
        })
        rzp.open()
      } else {
        // Demo mode - simulate success after delay
        setTimeout(async () => {
          try {
            const demoRes = await fetch(`/api/payments/demo-success/${orderResult!.id}`, { method: 'POST' })
            const demoData = await demoRes.json()
            if (demoRes.ok) {
              setStep('success')
              fetchCart()
            } else {
              setStep('failed')
              setPaymentError(formatApiError(demoData) || 'Demo payment failed')
            }
          } catch (e) {
            setStep('failed')
            setPaymentError('Demo payment simulation failed. Please try again.')
          }
          setProcessing(false)
        }, 1500)
      }
    })
    .catch(e => {
      setPaymentError('Failed to initialize payment. Please try again.')
      setProcessing(false)
    })
  }

  // Load Razorpay script
  useEffect(() => {
    const script = document.createElement('script')
    script.src = 'https://checkout.razorpay.com/v1/checkout.js'
    script.async = true
    document.body.appendChild(script)
    return () => { document.body.removeChild(script) }
  }, [])

  if (loading) {
    return (
      <div className="p-6 lg:p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-slate-200/70 rounded w-1/4"></div>
          <div className="h-64 bg-slate-200/70 rounded-lg"></div>
        </div>
      </div>
    )
  }

  const isEmpty = !cart || cart.items.length === 0

  return (
    <div className="p-6 lg:p-8 max-w-5xl mx-auto">
      {step === 'success' ? (
        <div className="card p-8 text-center">
          <div className="text-6xl mb-4">✅</div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Payment successful! Your order has been confirmed.</h2>
          <p className="text-slate-600 mb-1">Order #{orderResult?.id.slice(0, 8)}</p>
          <p className="text-slate-500 text-sm mb-6">Total: ₹{orderResult?.total.toLocaleString()}</p>
          <div className="flex gap-3 justify-center">
            <a href="/orders" className="btn-primary">View Orders</a>
            <a href="/products" className="btn-secondary">Continue Shopping</a>
          </div>
        </div>
      ) : step === 'failed' ? (
        <div className="card p-8 text-center">
          <div className="text-6xl mb-4">❌</div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Payment failed. Please try again.</h2>
          <p className="text-red-600 text-sm mb-6">{paymentError || 'Unknown error'}</p>
          <div className="flex gap-3 justify-center">
            <button onClick={() => { setStep('payment'); setPaymentError('') }} className="btn-primary">Retry Payment</button>
            <button onClick={() => { setStep('cart'); setPaymentError('') }} className="btn-secondary">Back to Cart</button>
          </div>
        </div>
      ) : step === 'payment' && orderResult ? (
        <div className="card p-6">
          <h2 className="text-xl font-bold text-slate-900 mb-4">Complete Payment</h2>
          <div className="bg-slate-100 rounded-lg p-4 mb-4">
            <div className="space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-slate-500">Order ID</span><span className="text-slate-900 font-mono">{orderResult.id.slice(0, 12)}...</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Subtotal</span><span className="text-slate-900">₹{orderResult.subtotal.toLocaleString()}</span></div>
              {orderResult.discount > 0 && <div className="flex justify-between"><span className="text-slate-500">Discount</span><span className="text-emerald-600">-₹{orderResult.discount.toLocaleString()}</span></div>}
              <div className="flex justify-between"><span className="text-slate-500">Tax (18%)</span><span className="text-slate-900">₹{orderResult.tax.toLocaleString()}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Shipping</span><span className="text-slate-900">{orderResult.shipping === 0 ? 'Free' : `₹${orderResult.shipping}`}</span></div>
              <div className="flex justify-between border-t border-slate-200 pt-2"><span className="text-slate-900 font-semibold">Total</span><span className="text-primary-700 font-bold text-lg">₹{orderResult.total.toLocaleString()}</span></div>
            </div>
          </div>

          {paymentError && (
            <div className="bg-red-50 border border-red-200 text-red-700 text-sm p-3 rounded-lg mb-4">{String(paymentError)}</div>
          )}

          <button onClick={initRazorpay} disabled={processing} className="btn-success w-full py-3 text-base">
            {processing ? '⏳ Processing...' : '💳 Pay with Razorpay'}
          </button>
          <p className="text-[10px] text-slate-400 text-center mt-2">TEST MODE — No real money charged</p>
        </div>
      ) : step === 'checkout' ? (
        <div className="card p-6">
          <h2 className="text-xl font-bold text-slate-900 mb-4">Checkout</h2>
          <div className="space-y-3 mb-6">
            <div>
              <label className="text-xs text-slate-500 mb-1 block">Full Name *</label>
              <input type="text" value={checkoutData.name} onChange={e => setCheckoutData({...checkoutData, name: e.target.value})} className="input" placeholder="John Doe" />
            </div>
            <div>
              <label className="text-xs text-slate-500 mb-1 block">Email *</label>
              <input type="email" value={checkoutData.email} onChange={e => setCheckoutData({...checkoutData, email: e.target.value})} className="input" placeholder="john@example.com" />
            </div>
            <div>
              <label className="text-xs text-slate-500 mb-1 block">Phone</label>
              <input type="tel" value={checkoutData.phone} onChange={e => setCheckoutData({...checkoutData, phone: e.target.value})} className="input" placeholder="+91 9876543210" />
            </div>
            <div>
              <label className="text-xs text-slate-500 mb-1 block">Address</label>
              <input type="text" value={checkoutData.address} onChange={e => setCheckoutData({...checkoutData, address: e.target.value})} className="input" placeholder="123 Main St, City" />
            </div>
          </div>
          <div className="bg-slate-100 rounded-lg p-3 mb-4">
            <div className="flex justify-between text-sm"><span className="text-slate-600">Total</span><span className="text-primary-700 font-bold">₹{cart?.total.toLocaleString()}</span></div>
          </div>
          {paymentError && <div className="bg-red-50 border border-red-200 text-red-700 text-sm p-3 rounded-lg mb-4">{String(paymentError)}</div>}
          <div className="flex gap-2">
            <button onClick={handleCheckout} disabled={processing} className="btn-primary flex-1 py-3">{processing ? 'Processing...' : 'Place Order →'}</button>
            <button onClick={() => { setStep('cart'); setPaymentError('') }} className="btn-secondary">Back</button>
          </div>
        </div>
      ) : isEmpty ? (
        <div className="card p-12 text-center">
          <div className="text-6xl mb-4">🛒</div>
          <h2 className="text-xl font-semibold text-slate-900 mb-2">Your cart is empty</h2>
          <p className="text-slate-500 text-sm mb-6">Browse our catalog and add some products!</p>
          <a href="/products" className="btn-primary inline-block">Browse Products</a>
        </div>
      ) : (
        <>
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Shopping Cart</h1>
              <p className="text-slate-500 text-sm mt-1">{cart!.item_count} items</p>
            </div>
            <button onClick={clearCart} className="btn-danger text-xs">Clear Cart</button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-3">
              {cart!.items.map(item => (
                <div key={item.id} className="card p-4 flex items-center gap-4">
                  <a href={`/product?id=${item.product_id}`} className="w-16 h-16 bg-slate-100 rounded-lg flex-shrink-0 overflow-hidden">
                    {item.image_url ? (
                      <img
                        src={item.image_url}
                        alt={item.product_name}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          const img = e.target as HTMLImageElement
                          img.onerror = null
                          img.src = 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"64\" height=\"64\" viewBox=\"0 0 64 64\"><rect fill=\"#1e1b4b\" width=\"64\" height=\"64\"/><text fill=\"#6366f1\" font-family=\"Arial\" font-size=\"20\" text-anchor=\"middle\" x=\"32\" y=\"37\">📦</text></svg>')
                        }}
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center bg-slate-100">
                        <span className="text-2xl">📦</span>
                      </div>
                    )}
                  </a>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-slate-900 text-sm truncate">{sanitizeProductName(item.product_name)}</h3>
                    <p className="text-xs text-slate-500">₹{item.price_at_time.toLocaleString()} each</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button onClick={() => updateQuantity(item.product_id, item.quantity - 1)}
                      className="w-8 h-8 bg-slate-100 border border-slate-200 rounded text-slate-700 hover:bg-slate-200 flex items-center justify-center text-sm">−</button>
                    <span className="w-8 text-center text-sm font-medium text-slate-900">{item.quantity}</span>
                    <button onClick={() => updateQuantity(item.product_id, item.quantity + 1)}
                      className="w-8 h-8 bg-slate-100 border border-slate-200 rounded text-slate-700 hover:bg-slate-200 flex items-center justify-center text-sm">+</button>
                  </div>
                  <div className="text-right min-w-[80px]">
                    <p className="text-sm font-semibold text-slate-900">₹{item.subtotal.toLocaleString()}</p>
                  </div>
                  <button onClick={() => removeItem(item.product_id)} className="text-slate-400 hover:text-red-600 text-sm">✕</button>
                </div>
              ))}
            </div>

            <div>
              <div className="card p-5 sticky top-6">
                <h3 className="font-semibold text-slate-900 mb-4">Order Summary</h3>
                <div className="space-y-2 text-sm mb-4">
                  <div className="flex justify-between"><span className="text-slate-500">Subtotal</span><span className="text-slate-900">₹{cart!.total.toLocaleString()}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Tax (18% GST)</span><span className="text-slate-900">₹{(cart!.total * 0.18).toFixed(2)}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Shipping</span><span className="text-emerald-600">{cart!.total >= 500 ? 'Free' : '₹49'}</span></div>
                  <div className="flex justify-between border-t border-slate-200 pt-2">
                    <span className="text-slate-900 font-semibold">Estimated Total</span>
                    <span className="text-primary-700 font-bold">₹{(cart!.total + cart!.total * 0.18 + (cart!.total >= 500 ? 0 : 49)).toFixed(2)}</span>
                  </div>
                </div>
                <button onClick={() => setStep('checkout')} className="btn-success w-full py-3 text-base">Proceed to Checkout →</button>
                <a href="/products" className="block text-center text-sm text-primary-700 hover:text-primary-600 mt-3">Continue Shopping</a>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
