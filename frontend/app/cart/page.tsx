'use client'

import { useEffect, useState } from 'react'

interface CartItem {
  id: string; product_id: string; product_name: string;
  quantity: number; price_at_time: number; subtotal: number;
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
          name: 'MerchantFlow AI',
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
            ondismiss: () => { setProcessing(false); setPaymentError('Payment cancelled. You can retry from the payment step.') },
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
          <div className="h-8 bg-dark-700 rounded w-1/4"></div>
          <div className="h-64 bg-dark-800 rounded-lg"></div>
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
          <h2 className="text-2xl font-bold text-white mb-2">Payment Successful!</h2>
          <p className="text-dark-300 mb-1">Order #{orderResult?.id.slice(0, 8)}</p>
          <p className="text-dark-400 text-sm mb-6">Total: ₹{orderResult?.total.toLocaleString()}</p>
          <div className="flex gap-3 justify-center">
            <a href="/orders" className="btn-primary">View Orders</a>
            <a href="/products" className="btn-secondary">Continue Shopping</a>
          </div>
        </div>
      ) : step === 'failed' ? (
        <div className="card p-8 text-center">
          <div className="text-6xl mb-4">❌</div>
          <h2 className="text-2xl font-bold text-white mb-2">Payment Failed</h2>
          <p className="text-red-400 text-sm mb-6">{paymentError || 'Unknown error'}</p>
          <button onClick={() => { setStep('cart'); setPaymentError('') }} className="btn-primary">Try Again</button>
        </div>
      ) : step === 'payment' && orderResult ? (
        <div className="card p-6">
          <h2 className="text-xl font-bold text-white mb-4">Complete Payment</h2>
          <div className="bg-dark-700 rounded-lg p-4 mb-4">
            <div className="space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-dark-400">Order ID</span><span className="text-white font-mono">{orderResult.id.slice(0, 12)}...</span></div>
              <div className="flex justify-between"><span className="text-dark-400">Subtotal</span><span className="text-white">₹{orderResult.subtotal.toLocaleString()}</span></div>
              {orderResult.discount > 0 && <div className="flex justify-between"><span className="text-dark-400">Discount</span><span className="text-emerald-400">-₹{orderResult.discount.toLocaleString()}</span></div>}
              <div className="flex justify-between"><span className="text-dark-400">Tax (18%)</span><span className="text-white">₹{orderResult.tax.toLocaleString()}</span></div>
              <div className="flex justify-between"><span className="text-dark-400">Shipping</span><span className="text-white">{orderResult.shipping === 0 ? 'Free' : `₹${orderResult.shipping}`}</span></div>
              <div className="flex justify-between border-t border-dark-600 pt-2"><span className="text-white font-semibold">Total</span><span className="text-primary-400 font-bold text-lg">₹{orderResult.total.toLocaleString()}</span></div>
            </div>
          </div>

          {paymentError && (
            <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-sm p-3 rounded-lg mb-4">{String(paymentError)}</div>
          )}

          <button onClick={initRazorpay} disabled={processing} className="btn-success w-full py-3 text-base">
            {processing ? '⏳ Processing...' : '💳 Pay with Razorpay'}
          </button>
          <p className="text-[10px] text-dark-500 text-center mt-2">TEST MODE — No real money charged</p>
        </div>
      ) : step === 'checkout' ? (
        <div className="card p-6">
          <h2 className="text-xl font-bold text-white mb-4">Checkout</h2>
          <div className="space-y-3 mb-6">
            <div>
              <label className="text-xs text-dark-400 mb-1 block">Full Name *</label>
              <input type="text" value={checkoutData.name} onChange={e => setCheckoutData({...checkoutData, name: e.target.value})} className="input" placeholder="John Doe" />
            </div>
            <div>
              <label className="text-xs text-dark-400 mb-1 block">Email *</label>
              <input type="email" value={checkoutData.email} onChange={e => setCheckoutData({...checkoutData, email: e.target.value})} className="input" placeholder="john@example.com" />
            </div>
            <div>
              <label className="text-xs text-dark-400 mb-1 block">Phone</label>
              <input type="tel" value={checkoutData.phone} onChange={e => setCheckoutData({...checkoutData, phone: e.target.value})} className="input" placeholder="+91 9876543210" />
            </div>
            <div>
              <label className="text-xs text-dark-400 mb-1 block">Address</label>
              <input type="text" value={checkoutData.address} onChange={e => setCheckoutData({...checkoutData, address: e.target.value})} className="input" placeholder="123 Main St, City" />
            </div>
          </div>
          <div className="bg-dark-700 rounded-lg p-3 mb-4">
            <div className="flex justify-between text-sm"><span className="text-dark-300">Total</span><span className="text-primary-400 font-bold">₹{cart?.total.toLocaleString()}</span></div>
          </div>
          {paymentError && <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-sm p-3 rounded-lg mb-4">{String(paymentError)}</div>}
          <div className="flex gap-2">
            <button onClick={handleCheckout} disabled={processing} className="btn-primary flex-1 py-3">{processing ? 'Processing...' : 'Place Order →'}</button>
            <button onClick={() => { setStep('cart'); setPaymentError('') }} className="btn-secondary">Back</button>
          </div>
        </div>
      ) : isEmpty ? (
        <div className="card p-12 text-center">
          <div className="text-6xl mb-4">🛒</div>
          <h2 className="text-xl font-semibold text-white mb-2">Your cart is empty</h2>
          <p className="text-dark-400 text-sm mb-6">Browse our catalog and add some products!</p>
          <a href="/products" className="btn-primary inline-block">Browse Products</a>
        </div>
      ) : (
        <>
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold text-white">Shopping Cart</h1>
              <p className="text-dark-400 text-sm mt-1">{cart!.item_count} items</p>
            </div>
            <button onClick={clearCart} className="btn-danger text-xs">Clear Cart</button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-3">
              {cart!.items.map(item => (
                <div key={item.id} className="card p-4 flex items-center gap-4">
                  <div className="w-16 h-16 bg-dark-700 rounded-lg flex items-center justify-center flex-shrink-0">
                    <span className="text-2xl">📦</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-white text-sm truncate">{item.product_name}</h3>
                    <p className="text-xs text-dark-400">₹{item.price_at_time.toLocaleString()} each</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button onClick={() => updateQuantity(item.product_id, item.quantity - 1)}
                      className="w-8 h-8 bg-dark-700 border border-dark-600 rounded text-dark-200 hover:bg-dark-600 flex items-center justify-center text-sm">−</button>
                    <span className="w-8 text-center text-sm font-medium text-white">{item.quantity}</span>
                    <button onClick={() => updateQuantity(item.product_id, item.quantity + 1)}
                      className="w-8 h-8 bg-dark-700 border border-dark-600 rounded text-dark-200 hover:bg-dark-600 flex items-center justify-center text-sm">+</button>
                  </div>
                  <div className="text-right min-w-[80px]">
                    <p className="text-sm font-semibold text-white">₹{item.subtotal.toLocaleString()}</p>
                  </div>
                  <button onClick={() => removeItem(item.product_id)} className="text-dark-500 hover:text-red-400 text-sm">✕</button>
                </div>
              ))}
            </div>

            <div>
              <div className="card p-5 sticky top-6">
                <h3 className="font-semibold text-white mb-4">Order Summary</h3>
                <div className="space-y-2 text-sm mb-4">
                  <div className="flex justify-between"><span className="text-dark-400">Subtotal</span><span className="text-white">₹{cart!.total.toLocaleString()}</span></div>
                  <div className="flex justify-between"><span className="text-dark-400">Tax (18% GST)</span><span className="text-white">₹{(cart!.total * 0.18).toFixed(2)}</span></div>
                  <div className="flex justify-between"><span className="text-dark-400">Shipping</span><span className="text-emerald-400">{cart!.total >= 500 ? 'Free' : '₹49'}</span></div>
                  <div className="flex justify-between border-t border-dark-600 pt-2">
                    <span className="text-white font-semibold">Estimated Total</span>
                    <span className="text-primary-400 font-bold">₹{(cart!.total + cart!.total * 0.18 + (cart!.total >= 500 ? 0 : 49)).toFixed(2)}</span>
                  </div>
                </div>
                <button onClick={() => setStep('checkout')} className="btn-success w-full py-3 text-base">Proceed to Checkout →</button>
                <a href="/products" className="block text-center text-sm text-primary-400 hover:text-primary-300 mt-3">Continue Shopping</a>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
