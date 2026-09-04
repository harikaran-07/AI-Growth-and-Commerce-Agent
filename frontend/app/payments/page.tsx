'use client'

import { useEffect, useState } from 'react'

interface Payment {
  id: string; order_id: string; amount: number; currency: string;
  status: string; razorpay_order_id: string | null;
  razorpay_payment_id: string | null; failure_reason: string | null; created_at: string;
}

export default function PaymentsPage() {
  const [payments, setPayments] = useState<Payment[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => { fetchPayments() }, [])

  const fetchPayments = async () => {
    try {
      const res = await fetch('/api/payments/')
      if (res.ok) { const data = await res.json(); setPayments(data) }
    } catch (e) { console.error('Failed') }
    finally { setLoading(false) }
  }

  const handleDemoFail = async (id: string) => {
    await fetch(`/api/payments/demo-fail/${id}`, { method: 'POST' })
    fetchPayments()
  }

  const statusColor = (s: string) => {
    const m: Record<string, string> = {
      initiated: 'badge-info', success: 'badge-success',
      failed: 'badge-danger', created: 'badge-neutral',
    }
    return m[s] || 'badge-neutral'
  }

  return (
    <div className="p-6 lg:p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Payment History</h1>
        <p className="text-slate-500 text-sm mt-1">Track all transactions · TEST MODE</p>
      </div>

      {loading ? (
        <div className="h-64 bg-slate-200/70 rounded-lg animate-pulse"></div>
      ) : payments.length === 0 ? (
        <div className="card p-12 text-center">
          <div className="text-6xl mb-4">💳</div>
          <p className="text-slate-600">No payments yet</p>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">ID</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Amount</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Razorpay ID</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {payments.map(p => (
                  <tr key={p.id} className="hover:bg-slate-100">
                    <td className="px-4 py-3 font-mono text-slate-700 text-xs">{p.id.slice(0, 8)}...</td>
                    <td className="px-4 py-3 font-semibold text-slate-900">₹{p.amount.toLocaleString()}</td>
                    <td className="px-4 py-3">
                      <span className={statusColor(p.status)}>{p.status}</span>
                      {p.failure_reason && <p className="text-xs text-red-600 mt-1">{p.failure_reason}</p>}
                    </td>
                    <td className="px-4 py-3 text-slate-600 font-mono text-xs">{p.razorpay_order_id || '-'}</td>
                    <td className="px-4 py-3 text-slate-500 text-xs">{p.created_at ? new Date(p.created_at).toLocaleString() : '-'}</td>
                    <td className="px-4 py-3">
                      {p.status === 'initiated' && (
                        <button onClick={() => handleDemoFail(p.id)} className="text-xs text-red-600 hover:text-red-700">Demo Fail</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
