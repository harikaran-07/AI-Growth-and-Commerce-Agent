'use client'

import { useEffect, useState } from 'react'

interface Analytics {
  total_orders: number; total_revenue: number; average_order_value: number;
  payment_success_rate: number; total_products: number; low_stock_products: number;
  total_items_sold: number; profit: number; margin: number; conversion_rate: number;
}

export default function AnalyticsPage() {
  const [data, setData] = useState<Analytics | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/analytics/').then(r => r.json()).then(setData).catch(() => {}).finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="p-6 lg:p-8">
      <div className="animate-pulse space-y-4">
        <div className="h-8 bg-dark-700 rounded w-1/4"></div>
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => <div key={i} className="h-32 bg-dark-800 rounded-lg border border-dark-700"></div>)}
        </div>
      </div>
    </div>
  )

  return (
    <div className="p-6 lg:p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Growth Analytics</h1>
        <p className="text-dark-400 text-sm mt-1">Revenue insights and performance metrics</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Revenue Metrics */}
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-white mb-4">Revenue Metrics</h3>
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
          <h3 className="text-sm font-semibold text-white mb-4">Payment & Conversion</h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1.5">
                <span className="text-dark-300">Success Rate</span>
                <span className="text-white font-semibold">{data?.payment_success_rate || 0}%</span>
              </div>
              <div className="w-full bg-dark-700 rounded-full h-2">
                <div className="bg-emerald-500 h-2 rounded-full transition-all" style={{ width: `${data?.payment_success_rate || 0}%` }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1.5">
                <span className="text-dark-300">Conversion Rate</span>
                <span className="text-white font-semibold">{data?.conversion_rate || 0}%</span>
              </div>
              <div className="w-full bg-dark-700 rounded-full h-2">
                <div className="bg-primary-500 h-2 rounded-full transition-all" style={{ width: `${Math.min(data?.conversion_rate || 0, 100)}%` }}></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* AI Agent Performance */}
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-white mb-4">System Performance</h3>
          <div className="space-y-3">
            <div className="p-3 bg-primary-500/5 border border-primary-500/10 rounded-lg">
              <div className="flex justify-between items-center">
                <span className="text-sm text-primary-300">Products in Catalog</span>
                <span className="text-lg font-bold text-primary-400">{data?.total_products || 0}</span>
              </div>
            </div>
            <div className="p-3 bg-amber-500/5 border border-amber-500/10 rounded-lg">
              <div className="flex justify-between items-center">
                <span className="text-sm text-amber-300">Low Stock Products</span>
                <span className="text-lg font-bold text-amber-400">{data?.low_stock_products || 0}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Safety & Policies */}
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-white mb-4">System Capabilities</h3>
          <div className="space-y-2">
            {[
              'Server-side price calculation',
              'Inventory validation before checkout',
              'Razorpay signature verification',
              'Audit trail for all actions',
              'Rule-based pricing recommendations',
              'Session-based cart persistence',
            ].map((item, i) => (
              <div key={i} className="flex items-center gap-2 text-sm text-dark-200">
                <span className="text-emerald-400">✓</span>
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
    emerald: 'text-emerald-400', primary: 'text-primary-400', amber: 'text-amber-400',
  }
  return (
    <div className="flex justify-between items-center p-2.5 bg-dark-700/30 rounded-lg">
      <span className="text-sm text-dark-300">{label}</span>
      <span className={`text-sm font-semibold ${color ? colorMap[color] || 'text-white' : 'text-white'}`}>{value}</span>
    </div>
  )
}
