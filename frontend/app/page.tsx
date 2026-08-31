'use client'

import { useEffect, useState } from 'react'

interface DashboardData {
  total_revenue: number
  total_orders: number
  average_order_value: number
  profit: number
  margin: number
  products_sold: number
  low_stock_products: number
  conversion_rate: number
  revenue_chart: { label: string; revenue: number; orders: number }[]
  recent_orders: { id: string; total: number; status: string; created_at: string }[]
  top_products: { name: string; revenue: number; sales: number; stock: number }[]
  notifications_count: number
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [chartPeriod, setChartPeriod] = useState('30d')

  useEffect(() => { fetchData() }, [])

  const fetchData = async () => {
    try {
      const res = await fetch('/api/analytics/dashboard')
      const d = await res.json()
      setData(d)
    } catch (e) {
      console.error('Failed to fetch dashboard')
    } finally { setLoading(false) }
  }

  if (loading) {
    return (
      <div className="p-6 lg:p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-dark-700 rounded w-1/4"></div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="h-28 bg-dark-800 rounded-lg border border-dark-700"></div>
            ))}
          </div>
          <div className="h-72 bg-dark-800 rounded-lg border border-dark-700"></div>
        </div>
      </div>
    )
  }

  const chart = data?.revenue_chart || []
  const maxRev = Math.max(...chart.map(c => c.revenue), 1)

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Merchant Overview</h1>
            <p className="text-dark-400 mt-1 text-sm">TechZone Electronics — AI-Powered Growth Analytics</p>
          </div>
          <button onClick={fetchData} className="btn-secondary text-xs">
            ↻ Refresh
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <MetricCard
          title="Total Revenue"
          value={`₹${(data?.total_revenue || 0).toLocaleString()}`}
          icon="💰"
          trend="+12.5%"
          trendUp
          color="emerald"
        />
        <MetricCard
          title="Orders"
          value={data?.total_orders || 0}
          icon="📦"
          trend={`${data?.total_orders || 0} total`}
          color="blue"
        />
        <MetricCard
          title="Avg Order Value"
          value={`₹${(data?.average_order_value || 0).toLocaleString()}`}
          icon="📊"
          trend="Per order"
          color="purple"
        />
        <MetricCard
          title="Profit"
          value={`₹${(data?.profit || 0).toLocaleString()}`}
          icon="📈"
          trend={`${(data?.margin || 0).toFixed(1)}% margin`}
          trendUp={data ? data.margin > 0 : false}
          color="amber"
        />
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <MetricCard title="Products Sold" value={data?.products_sold || 0} icon="🏷️" color="cyan" />
        <MetricCard title="Low Stock" value={data?.low_stock_products || 0} icon="⚠️" color={data && data.low_stock_products > 10 ? "red" : "amber"} />
        <MetricCard title="Conversion" value={`${data?.conversion_rate || 0}%`} icon="🎯" color="pink" />
        <MetricCard title="Notifications" value={data?.notifications_count || 0} icon="🔔" color="orange" />
      </div>

      {/* Revenue Chart */}
      <div className="card p-5 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-white">Revenue Trend</h3>
          <div className="flex gap-1">
            {['7d', '30d', '90d', '1y'].map(p => (
              <button
                key={p}
                onClick={() => setChartPeriod(p)}
                className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                  chartPeriod === p
                    ? 'bg-primary-600 text-white'
                    : 'bg-dark-700 text-dark-300 hover:bg-dark-600'
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>
        <div className="flex items-end gap-1 h-48">
          {chart.slice(-30).map((point, i) => (
            <div key={i} className="flex-1 flex flex-col items-center gap-1 group relative">
              <div className="absolute bottom-full mb-2 hidden group-hover:block bg-dark-800 border border-dark-600 rounded px-2 py-1 text-[10px] text-dark-200 whitespace-nowrap z-10">
                {point.label}: ₹{point.revenue.toLocaleString()}
              </div>
              <div
                className="w-full bg-gradient-to-t from-primary-600 to-primary-400 rounded-t-sm transition-all duration-300 hover:from-primary-500 hover:to-primary-300"
                style={{
                  height: `${Math.max((point.revenue / maxRev) * 100, 2)}%`,
                  minHeight: '2px',
                }}
              />
            </div>
          ))}
        </div>
        <div className="flex justify-between mt-2 text-[10px] text-dark-500">
          {chart.length > 0 && (
            <>
              <span>{chart[0]?.label}</span>
              <span>{chart[chart.length - 1]?.label}</span>
            </>
          )}
        </div>
      </div>

      {/* Bottom Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Products */}
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-white mb-4">Top Products by Revenue</h3>
          {data?.top_products && data.top_products.length > 0 ? (
            <div className="space-y-3">
              {data.top_products.map((p, i) => (
                <div key={i} className="flex items-center gap-3 p-2.5 bg-dark-700/50 rounded-lg">
                  <div className="w-8 h-8 rounded bg-primary-600/20 flex items-center justify-center text-primary-400 text-xs font-bold">
                    #{i + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-dark-100 truncate">{p.name}</p>
                    <p className="text-xs text-dark-400">{p.sales} sales · {p.stock} stock</p>
                  </div>
                  <span className="text-sm font-semibold text-emerald-400">₹{p.revenue.toLocaleString()}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-dark-400 text-center py-6">No sales data yet</p>
          )}
        </div>

        {/* Recent Orders */}
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-white mb-4">Recent Orders</h3>
          {data?.recent_orders && data.recent_orders.length > 0 ? (
            <div className="space-y-2">
              {data.recent_orders.map((o, i) => (
                <div key={i} className="flex items-center gap-3 p-2.5 bg-dark-700/50 rounded-lg">
                  <div className={`w-2 h-2 rounded-full ${
                    o.status === 'success' ? 'bg-emerald-400' :
                    o.status === 'failed' ? 'bg-red-400' :
                    o.status === 'pending' ? 'bg-amber-400' : 'bg-dark-400'
                  }`}></div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-dark-100">Order {o.id}</p>
                    <p className="text-xs text-dark-400">{o.created_at ? new Date(o.created_at).toLocaleDateString() : '-'}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-white">₹{o.total.toLocaleString()}</p>
                    <p className={`text-[10px] font-medium ${
                      o.status === 'success' ? 'text-emerald-400' :
                      o.status === 'failed' ? 'text-red-400' : 'text-amber-400'
                    }`}>{o.status}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-dark-400 text-center py-6">No orders yet — make a test purchase!</p>
          )}
        </div>
      </div>
    </div>
  )
}

function MetricCard({ title, value, icon, trend, trendUp, color }: {
  title: string; value: string | number; icon: string; trend?: string; trendUp?: boolean; color: string
}) {
  const colorMap: Record<string, string> = {
    emerald: 'from-emerald-500/10 to-emerald-500/5 border-emerald-500/20',
    blue: 'from-blue-500/10 to-blue-500/5 border-blue-500/20',
    purple: 'from-purple-500/10 to-purple-500/5 border-purple-500/20',
    amber: 'from-amber-500/10 to-amber-500/5 border-amber-500/20',
    cyan: 'from-cyan-500/10 to-cyan-500/5 border-cyan-500/20',
    red: 'from-red-500/10 to-red-500/5 border-red-500/20',
    pink: 'from-pink-500/10 to-pink-500/5 border-pink-500/20',
    orange: 'from-orange-500/10 to-orange-500/5 border-orange-500/20',
  }

  return (
    <div className={`bg-gradient-to-br ${colorMap[color] || colorMap.blue} border rounded-lg p-4`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-dark-400 font-medium">{title}</p>
          <p className="text-xl font-bold text-white mt-1">{value}</p>
          {trend && (
            <p className={`text-[11px] mt-1 ${trendUp ? 'text-emerald-400' : 'text-dark-400'}`}>
              {trendUp && '↑ '}{trend}
            </p>
          )}
        </div>
        <span className="text-xl">{icon}</span>
      </div>
    </div>
  )
}
