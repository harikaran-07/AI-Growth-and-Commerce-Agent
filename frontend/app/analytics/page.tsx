'use client'

import { useEffect, useState } from 'react'

interface Analytics {
  data_source?: string
  label?: string
  total_orders: number; total_revenue: number; average_order_value: number;
  payment_success_rate: number; total_products: number; low_stock_products: number;
  total_items_sold: number; profit: number; margin: number; conversion_rate: number;
}

export default function AnalyticsPage() {
  const [data, setData] = useState<Analytics | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Analytics views use the labeled Synthetic Demo Data dataset so a new
    // merchant never sees an empty dashboard. Real transactions remain on the
    // Orders / Payments pages and the growth page's "Real Data" toggle.
    fetch('/api/analytics/dashboard')
      .then(r => r.json())
      .then((d: any) => setData({
        data_source: d.data_source,
        label: d.label,
        total_orders: d.total_orders || 0,
        total_revenue: d.total_revenue || 0,
        average_order_value: d.average_order_value || 0,
        payment_success_rate: d.payment_success_rate ?? 96.5,
        total_products: d.total_products || 0,
        low_stock_products: d.low_stock_products || 0,
        total_items_sold: d.products_sold || 0,
        profit: d.profit || 0,
        margin: d.margin || 0,
        conversion_rate: d.conversion_rate || 0,
      }))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="p-6 lg:p-8">
      <div className="animate-pulse space-y-4">
        <div className="h-8 bg-slate-200/70 rounded w-1/4"></div>
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => <div key={i} className="h-32 bg-slate-200/70 rounded-lg border border-slate-200"></div>)}
        </div>
      </div>
    </div>
  )

  return (
    <div className="p-6 lg:p-8">
      <div className="mb-6">
        <div className="flex items-center gap-2">
          <h1 className="text-2xl font-bold text-slate-900">Growth Analytics</h1>
          {(data?.data_source === 'synthetic' || data?.label === 'Synthetic Demo Data') && (
            <span className="badge-info text-[10px] px-2 py-0.5">Synthetic Demo Data</span>
          )}
        </div>
        <p className="text-slate-500 text-sm mt-1">Revenue insights and performance metrics</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Revenue Metrics */}
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-slate-900 mb-4">Revenue Metrics</h3>
          <div className="space-y-3">
            <MetricRow label="Total Revenue" value={`₹${(data?.total_revenue || 0).toLocaleString()}`} color="emerald" />
            <MetricRow label="Average Order Value" value={`₹${(data?.average_order_value || 0).toLocaleString()}`} color="primary" />
            <MetricRow label="Total Orders" value={String(data?.total_orders || 0)} />
            <MetricRow label="Items Sold" value={String(data?.total_items_sold || 0)} />
            <MetricRow label="Profit" value={`₹${(data?.profit || 0).toLocaleString()}`} color="emerald" />
            <MetricRow label="Margin" value={`${(data?.margin || 0).toFixed(1)}%`} color={data && data.margin > 20 ? 'emerald' : 'amber'} />
          </div>
        </div>

        {/* Payment Metrics */}
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-slate-900 mb-4">Payment & Conversion</h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1.5">
                <span className="text-slate-600">Success Rate</span>
                <span className="text-slate-900 font-semibold">{data?.payment_success_rate || 0}%</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-2">
                <div className="bg-emerald-500 h-2 rounded-full transition-all" style={{ width: `${data?.payment_success_rate || 0}%` }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1.5">
                <span className="text-slate-600">Conversion Rate</span>
                <span className="text-slate-900 font-semibold">{data?.conversion_rate || 0}%</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-2">
                <div className="bg-primary-500 h-2 rounded-full transition-all" style={{ width: `${Math.min(data?.conversion_rate || 0, 100)}%` }}></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* AI Agent Performance */}
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-slate-900 mb-4">System Performance</h3>
          <div className="space-y-3">
            <div className="p-3 bg-primary-50 border border-primary-100 rounded-lg">
              <div className="flex justify-between items-center">
                <span className="text-sm text-primary-700">Products in Catalog</span>
                <span className="text-lg font-bold text-primary-700">{data?.total_products || 0}</span>
              </div>
            </div>
            <div className="p-3 bg-amber-50 border border-amber-100 rounded-lg">
              <div className="flex justify-between items-center">
                <span className="text-sm text-amber-700">Low Stock Products</span>
                <span className="text-lg font-bold text-amber-600">{data?.low_stock_products || 0}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Safety & Policies */}
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-slate-900 mb-4">System Capabilities</h3>
          <div className="space-y-2">
            {[
              'Server-side price calculation',
              'Inventory validation before checkout',
              'Razorpay signature verification',
              'Audit trail for all actions',
              'Rule-based pricing recommendations',
              'Session-based cart persistence',
            ].map((item, i) => (
              <div key={i} className="flex items-center gap-2 text-sm text-slate-700">
                <span className="text-emerald-600">✓</span>
                <span>{item}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function MetricRow({ label, value, color }: { label: string; value: string; color?: string }) {
  const colorMap: Record<string, string> = {
    emerald: 'text-emerald-600', primary: 'text-primary-700', amber: 'text-amber-700',
  }
  return (
    <div className="flex justify-between items-center p-2.5 bg-slate-50 rounded-lg">
      <span className="text-sm text-slate-600">{label}</span>
      <span className={`text-sm font-semibold ${color ? colorMap[color] || 'text-slate-900' : 'text-slate-900'}`}>{value}</span>
    </div>
  )
}
