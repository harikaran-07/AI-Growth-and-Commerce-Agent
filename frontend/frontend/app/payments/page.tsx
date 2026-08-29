'use client'

import { useEffect, useState } from 'react'

interface Payment {
  id: string
  order_id: string
  amount: number
  currency: string
  status: string
  razorpay_order_id: string | null
  razorpay_payment_id: string | null
  failure_reason: string | null
  created_at: string
}

export default function PaymentsPage() {
  const [payments, setPayments] = useState<Payment[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchPayments()
  }, [])

  const fetchPayments = async () => {
    try {
      const res = await fetch('/api/payments/')
      if (res.ok) {
        const data = await res.json()
        setPayments(data)
      }
    } catch (error) {
      console.error('Failed to fetch payments')
    } finally {
      setLoading(false)
    }
  }

  const handleDemoFail = async (paymentId: string) => {
    try {
      await fetch(`/api/payments/demo-fail/${paymentId}`, { method: 'POST' })
      fetchPayments()
    } catch (error) {
      console.error('Failed to demo fail payment')
    }
  }

  const statusColors: Record<string, string> = {
    initiated: 'bg-blue-100 text-blue-800',
    success: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
    created: 'bg-gray-100 text-gray-800',
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

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Payment History</h1>
        <p className="text-gray-600 mt-1">Track all test mode transactions</p>
        <span className="inline-block mt-2 px-2 py-1 bg-yellow-100 text-yellow-800 text-xs font-medium rounded">
          TEST MODE - No real money
        </span>
      </div>

      {payments.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <div className="text-6xl mb-4">💳</div>
          <p className="text-gray-600">No payments yet</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Razorpay Order</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {payments.map((payment) => (
                <tr key={payment.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-mono text-gray-900">
                    {payment.id.slice(0, 8)}...
                  </td>
                  <td className="px-6 py-4 text-sm font-semibold text-gray-900">
                    ₹{payment.amount.toLocaleString()}
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 text-xs font-medium rounded ${statusColors[payment.status] || 'bg-gray-100 text-gray-800'}`}>
                      {payment.status.toUpperCase()}
                    </span>
                    {payment.failure_reason && (
                      <p className="text-xs text-red-600 mt-1">{payment.failure_reason}</p>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600 font-mono">
                    {payment.razorpay_order_id || '-'}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {new Date(payment.created_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-4">
                    {payment.status === 'initiated' && (
                      <button
                        onClick={() => handleDemoFail(payment.id)}
                        className="text-sm text-red-600 hover:underline"
                      >
                        Demo Fail
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
