'use client'

import { useEffect, useState } from 'react'

interface CartItem {
  id: string
  product_id: string
  product_name: string
  quantity: number
  price_at_time: number
  subtotal: number
}

interface Cart {
  id: string
  status: string
  total: number
  items: CartItem[]
  item_count: number
}

export default function CartPage() {
  const [cart, setCart] = useState<Cart | null>(null)
  const [loading, setLoading] = useState(true)
  const [approving, setApproving] = useState(false)
  const [paymentStatus, setPaymentStatus] = useState<string | null>(null)

  useEffect(() => {
    fetchCart()
  }, [])

  const fetchCart = async () => {
    try {
      const cartId = localStorage.getItem('cartId')
      if (!cartId) {
        setLoading(false)
        return
      }
      const res = await fetch(`/api/carts/${cartId}`)
      if (res.ok) {
        const data = await res.json()
        setCart(data)
      }
    } catch (error) {
      console.error('Failed to fetch cart')
    } finally {
      setLoading(false)
    }
  }

  const handleApprovePayment = async () => {
    if (!cart) return
    setApproving(true)
    
    try {
      const approvalRes = await fetch('/api/agent/request-approval', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          cart_id: cart.id,
          session_id: `session_${Date.now()}`
        })
      })
      const approvalData = await approvalRes.json()

      if (approvalData.approval_id) {
        const approveRes = await fetch(`/api/approvals/${approvalData.approval_id}/approve`, {
          method: 'POST'
        })
        
        if (approveRes.ok) {
          const paymentRes = await fetch('/api/payments/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ order_id: approvalData.order_id })
          })
          const paymentData = await paymentRes.json()
          setPaymentStatus(paymentData.status)
        }
      }
    } catch (error) {
      console.error('Failed to process payment')
    } finally {
      setApproving(false)
    }
  }

  if (loading) {
    return (
      <div className="p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  if (!cart || cart.items.length === 0) {
    return (
      <div className="p-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Shopping Cart</h1>
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🛒</div>
          <p className="text-gray-600">Your cart is empty</p>
          <a href="/buyer" className="mt-4 inline-block px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
            Start Shopping
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Shopping Cart</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b">
              <h2 className="font-semibold">Cart Items ({cart.item_count})</h2>
            </div>
            <div className="divide-y">
              {cart.items.map((item) => (
                <div key={item.id} className="p-4 flex items-center justify-between">
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900">{item.product_name}</h3>
                    <p className="text-sm text-gray-600">₹{item.price_at_time.toLocaleString()} × {item.quantity}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold">₹{item.subtotal.toLocaleString()}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div>
          <div className="bg-white rounded-lg shadow p-6 sticky top-8">
            <h2 className="font-semibold mb-4">Order Summary</h2>
            
            <div className="space-y-2 mb-4">
              <div className="flex justify-between text-sm">
                <span>Subtotal</span>
                <span>₹{cart.total.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Shipping</span>
                <span className="text-green-600">Free</span>
              </div>
              <div className="border-t pt-2 mt-2">
                <div className="flex justify-between font-semibold">
                  <span>Total</span>
                  <span className="text-primary-600">₹{cart.total.toLocaleString()}</span>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 rounded p-3 mb-4">
              <p className="text-xs text-gray-600 mb-2">Policy Status:</p>
              <div className="flex items-center gap-2 text-sm">
                <span className="text-green-500">✓</span>
                <span>Within spending limit</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <span className="text-green-500">✓</span>
                <span>Products available</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <span className="text-green-500">✓</span>
                <span>Approval required</span>
              </div>
            </div>

            {paymentStatus === 'initiated' ? (
              <div className="text-center py-4">
                <div className="text-4xl mb-2">✅</div>
                <p className="font-semibold text-green-600">Payment Processing</p>
                <p className="text-sm text-gray-600">Your order is being processed</p>
              </div>
            ) : paymentStatus === 'failed' ? (
              <div className="text-center py-4">
                <div className="text-4xl mb-2">❌</div>
                <p className="font-semibold text-red-600">Payment Failed</p>
                <p className="text-sm text-gray-600 mb-4">Payment could not be completed</p>
                <button
                  onClick={() => setPaymentStatus(null)}
                  className="px-6 py-2 bg-primary-600 text-white rounded hover:bg-primary-700"
                >
                  Try Again
                </button>
              </div>
            ) : (
              <button
                onClick={handleApprovePayment}
                disabled={approving}
                className="w-full px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                {approving ? 'Processing...' : '✓ Approve Payment'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
