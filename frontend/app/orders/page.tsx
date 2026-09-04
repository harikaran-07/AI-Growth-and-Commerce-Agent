'use client'

import { useEffect, useState } from 'react'
import { sanitizeProductName } from '../utils'

interface OrderItem {
  id: string; product_id: string; product_name: string; quantity: number; price: number; subtotal: number;
}

interface Order {
  id: string; customer_name: string; customer_email: string; subtotal: number; discount: number;
  tax: number; shipping: number; total: number; status: string; payment_status: string;
  razorpay_order_id: string; items: OrderItem[]; created_at: string;
}

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null)
  const [statusFilter, setStatusFilter] = useState('')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(1)

  useEffect(() => { fetchOrders() }, [page, statusFilter])

  const fetchOrders = async () => {
    try {
      const params = new URLSearchParams({ page: String(page), page_size: '15' })
      if (statusFilter) params.set('status', statusFilter)
      const res = await fetch(`/api/orders/?${params}`)
      const data = await res.json()
      setOrders(data.orders || [])
      setTotal(data.total || 0)
      setTotalPages(data.total_pages || 1)
    } catch (e) { console.error('Failed to fetch orders') }
    finally { setLoading(false) }
  }

  const statusColor = (s: string) => {
    const m: Record<string, string> = {
      success: 'badge-success', paid: 'badge-success', delivered: 'badge-success',
      pending: 'badge-warning', processing: 'badge-warning',
      failed: 'badge-danger', payment_failed: 'badge-danger', cancelled: 'badge-danger',
    }
    return m[s] || 'badge-neutral'
  }

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

  return (
    <div className="p-6 lg:p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Orders</h1>
          <p className="text-slate-500 text-sm mt-1">{total} total orders</p>
        </div>
        <select value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(1) }} className="input w-48">
          <option value="">All Status</option>
          <option value="success">Paid</option>
          <option value="pending">Pending</option>
          <option value="processing">Processing</option>
          <option value="failed">Failed</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>

      {orders.length === 0 ? (
        <div className="card p-12 text-center">
          <div className="text-6xl mb-4">📋</div>
          <p className="text-slate-600 text-lg">No orders yet</p>
          <p className="text-slate-400 text-sm mt-1">Make a test purchase to see orders here</p>
          <a href="/products" className="btn-primary inline-block mt-4">Browse Products</a>
        </div>
      ) : (
        <>
          <div className="card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200">
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Order ID</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Customer</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Items</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Total</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Status</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {orders.map(order => (
                    <tr key={order.id} className="hover:bg-slate-100 cursor-pointer transition-colors" onClick={() => setSelectedOrder(order)}>
                      <td className="px-4 py-3 font-mono text-slate-700">{order.id.slice(0, 8)}...</td>
                      <td className="px-4 py-3 text-slate-700">{order.customer_name || '-'}</td>
                      <td className="px-4 py-3 text-slate-600">{order.items?.length || 0}</td>
                      <td className="px-4 py-3 font-semibold text-slate-900">₹{order.total.toLocaleString()}</td>
                      <td className="px-4 py-3"><span className={statusColor(order.status)}>{order.status}</span></td>
                      <td className="px-4 py-3 text-slate-500 text-xs">{order.created_at ? new Date(order.created_at).toLocaleDateString() : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-4">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="btn-secondary text-xs px-3 py-1.5">← Prev</button>
              <span className="text-sm text-slate-600">Page {page} of {totalPages}</span>
              <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages} className="btn-secondary text-xs px-3 py-1.5">Next →</button>
            </div>
          )}
        </>
      )}

      {/* Order Detail Modal */}
      {selectedOrder && (
        <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center z-50 p-4" onClick={() => setSelectedOrder(null)}>
          <div className="bg-white border border-slate-200 rounded-xl max-w-lg w-full max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h2 className="text-lg font-bold text-slate-900">Order Details</h2>
                  <p className="text-xs text-slate-500 font-mono">{selectedOrder.id}</p>
                </div>
                <button onClick={() => setSelectedOrder(null)} className="text-slate-500 hover:text-slate-900 text-xl">✕</button>
              </div>

              <div className="space-y-2 text-sm mb-4">
                <div className="flex justify-between"><span className="text-slate-500">Customer</span><span className="text-slate-900">{selectedOrder.customer_name || '-'}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Email</span><span className="text-slate-900">{selectedOrder.customer_email || '-'}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Status</span><span className={statusColor(selectedOrder.status)}>{selectedOrder.status}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Payment</span><span className={statusColor(selectedOrder.payment_status)}>{selectedOrder.payment_status}</span></div>
              </div>

              <h3 className="text-sm font-semibold text-slate-900 mb-2">Items</h3>
              <div className="space-y-2 mb-4">
                {selectedOrder.items?.map(item => (
                  <div key={item.id} className="flex items-center justify-between bg-slate-100 rounded p-2.5">
                    <div>
                      <p className="text-sm text-slate-900">{sanitizeProductName(item.product_name)}</p>
                      <p className="text-xs text-slate-500">₹{item.price.toLocaleString()} × {item.quantity}</p>
                    </div>
                    <span className="text-sm font-semibold text-slate-900">₹{item.subtotal.toLocaleString()}</span>
                  </div>
                ))}
              </div>

              <div className="space-y-1.5 text-sm border-t border-slate-200 pt-3">
                <div className="flex justify-between"><span className="text-slate-500">Subtotal</span><span className="text-slate-900">₹{selectedOrder.subtotal.toLocaleString()}</span></div>
                {selectedOrder.discount > 0 && <div className="flex justify-between"><span className="text-slate-500">Discount</span><span className="text-emerald-600">-₹{selectedOrder.discount.toLocaleString()}</span></div>}
                <div className="flex justify-between"><span className="text-slate-500">Tax</span><span className="text-slate-900">₹{selectedOrder.tax.toLocaleString()}</span></div>
                <div className="flex justify-between border-t border-slate-200 pt-2"><span className="text-slate-900 font-semibold">Total</span><span className="text-primary-700 font-bold">₹{selectedOrder.total.toLocaleString()}</span></div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
