'use client'

import { useEffect, useState } from 'react'
import { sanitizeProductName, formatPrice, formatNumber } from './utils'

interface CustomerSeg {
  name: string
  count: number
}

interface Customers {
  total: number
  new: number
  returning: number
  repeat_purchase_rate: number
  avg_customer_value: number
  segments: CustomerSeg[]
}

interface FunnelStage {
  stage: string
  count: number
  pct: number
}

interface DashboardData {
  data_source?: string
  label?: string
  disclaimer?: string
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
  top_products: { id?: string; name: string; image_url?: string; revenue: number; sales: number; stock: number; price?: number }[]
  notifications_count: number
  pending_orders: number
  completed_orders: number
  cancelled_orders: number
  total_customers: number
  best_sellers: { id?: string; name: string; image_url?: string; sales: number; revenue: number; category: string; stock: number }[]
  slow_movers: { id?: string; name: string; image_url?: string; sales: number; stock: number; category: string }[]
  low_stock_list: { id?: string; name: string; image_url?: string; stock: number; category: string; sales: number; status?: string }[]
  category_revenue: { category: string; revenue: number; sales: number }[]
  profit_analytics: { revenue: number; cogs: number; gross_profit: number; margin: number; has_cost_data: boolean }
  customers?: Customers
  funnel?: FunnelStage[]
  growth_insights?: string[]
  growth_opportunities?: { opportunity: string; impact: string; reason: string; action: string }[]
}

function ProductImage({ src, alt, className }: { src?: string; alt: string; className?: string }) {
  const [broken, setBroken] = useState(false)
  if (!src || broken) {
    return (
      <div className={`${className || 'w-10 h-10'} rounded-lg bg-dark-700 flex items-center justify-center text-dark-400 text-lg`}>
        📦
      </div>
    )
  }
  return (
    <img
      src={src}
      alt={alt}
      loading="lazy"
      className={`${className || 'w-10 h-10'} rounded-lg object-cover bg-dark-700`}
      onError={() => setBroken(true)}
    />
  )
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [chartPeriod, setChartPeriod] = useState('30d')
  const [chartData, setChartData] = useState<{ label: string; revenue: number; orders: number }[]>([])

  useEffect(() => { fetchData() }, [])

  useEffect(() => {
    if (data) fetchChartData()
  }, [chartPeriod, data])

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/analytics/dashboard')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const d = await res.json()
      setData(d)
      setChartData(d.revenue_chart || [])
    } catch (e) {
      console.error('Failed to fetch dashboard', e)
      setError('Unable to load analytics')
    } finally { setLoading(false) }
  }

  const fetchChartData = async () => {
    try {
      const res = await fetch(`/api/analytics/revenue-chart?period=${chartPeriod}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const d = await res.json()
      setChartData(d || [])
    } catch (e) {
      console.error('Failed to fetch chart data')
    }
  }

  const isLoading = loading && !data
  const isSynthetic = data?.data_source === 'synthetic' || data?.label === 'Synthetic Demo Data'

  if (isLoading) {
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

  if (error && !data) {
    return (
      <div className="p-6 lg:p-8 flex items-center justify-center min-h-[50vh]">
        <div className="text-center max-w-sm">
          <div className="text-4xl mb-3">📊</div>
          <h2 className="text-lg font-semibold text-white mb-1">Unable to load analytics</h2>
          <p className="text-sm text-dark-400 mb-4">The dashboard could not reach the analytics service. Please try again.</p>
          <button onClick={fetchData} className="btn-primary text-sm">↻ Retry</button>
        </div>
      </div>
    )
  }

  if (!data) return null

  const chart = chartData
  const maxRev = Math.max(...chart.map(c => c.revenue), 1)
  const customers = data.customers
  const funnel = data.funnel || []

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-2xl font-bold text-white">Dashboard</h1>
              {isSynthetic && (
                <span className="badge-info text-[10px] px-2 py-0.5">Synthetic Demo Data</span>
              )}
            </div>
            <p className="text-dark-400 mt-1 text-sm">AI Growth and Commerce Agent — Commerce Intelligence</p>
          </div>
          <button onClick={fetchData} className="btn-secondary text-xs">↻ Refresh</button>
        </div>
        {data.disclaimer && (
          <p className="text-[11px] text-amber-400/80 mt-2">{data.disclaimer}</p>
        )}
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <MetricCard
          title="Total Revenue"
          value={`₹${formatNumber(data.total_revenue)}`}
          icon="💰"
          trend={`${data.completed_orders} completed orders (90 days)`}
          trendUp={data.total_revenue > 0}
          color="emerald"
        />
        <MetricCard
          title="Orders"
          value={formatNumber(data.total_orders)}
          icon="📦"
          trend={`${data.pending_orders} pending · ${data.cancelled_orders} cancelled`}
          color="blue"
        />
        <MetricCard
          title="Avg Order Value"
          value={`₹${formatNumber(data.average_order_value)}`}
          icon="📊"
          trend="Per order"
          color="purple"
        />
        <MetricCard
          title="Profit"
          value={`₹${formatNumber(data.profit)}`}
          icon="📈"
          trend={`${data.margin.toFixed(1)}% margin`}
          trendUp={data.margin > 0}
          color="amber"
        />
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <MetricCard title="Products Sold" value={formatNumber(data.products_sold)} icon="🏷️" color="cyan" />
        <MetricCard
          title="Low Stock"
          value={formatNumber(data.low_stock_products)}
          icon="⚠️"
          color={data.low_stock_products > 10 ? 'red' : 'amber'}
        />
        <MetricCard title="Conversion" value={`${data.conversion_rate}%`} icon="🎯" color="pink" />
        <MetricCard title="Customers" value={formatNumber(data.total_customers)} icon="👥" color="orange" />
      </div>

      {/* Profit Analytics */}
      {data.profit_analytics && (
        <div className="card p-5 mb-6">
          <h3 className="text-sm font-semibold text-white mb-4">Profit Analytics</h3>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-dark-700/50 rounded-lg p-3">
              <p className="text-[10px] text-dark-400 mb-1">Revenue</p>
              <p className="text-lg font-bold text-emerald-400">₹{formatNumber(data.profit_analytics.revenue)}</p>
            </div>
            <div className="bg-dark-700/50 rounded-lg p-3">
              <p className="text-[10px] text-dark-400 mb-1">COGS</p>
              <p className="text-lg font-bold text-amber-400">₹{formatNumber(data.profit_analytics.cogs)}</p>
            </div>
            <div className="bg-dark-700/50 rounded-lg p-3">
              <p className="text-[10px] text-dark-400 mb-1">Gross Profit</p>
              <p className="text-lg font-bold text-primary-400">₹{formatNumber(data.profit_analytics.gross_profit)}</p>
            </div>
            <div className="bg-dark-700/50 rounded-lg p-3">
              <p className="text-[10px] text-dark-400 mb-1">Profit Margin</p>
              <p className="text-lg font-bold text-cyan-400">{data.profit_analytics.margin.toFixed(1)}%</p>
            </div>
          </div>
          {!data.profit_analytics.has_cost_data && (
            <p className="text-xs text-amber-400 mt-3">⚠️ Cost data unavailable for some products. Profit calculations may be incomplete.</p>
          )}
        </div>
      )}

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
        {chart.length === 0 || chart.every(c => c.revenue === 0) ? (
          <div className="text-center py-12">
            <p className="text-dark-400 text-sm">No sales data available for this period.</p>
          </div>
        ) : (
          <>
            <div className="flex items-end gap-px h-48">
              {chart.map((point, i) => (
                <div key={i} className="flex-1 flex flex-col items-center gap-1 group relative">
                  <div className="absolute bottom-full mb-2 hidden group-hover:block bg-dark-800 border border-dark-600 rounded px-2 py-1 text-[10px] text-dark-200 whitespace-nowrap z-10">
                    {point.label}: ₹{formatNumber(point.revenue)}
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
          </>
        )}
      </div>

      {/* Customers + Funnel */}
      {customers && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div className="card p-5">
            <h3 className="text-sm font-semibold text-white mb-4">👥 Customer Analytics</h3>
            <div className="grid grid-cols-2 gap-3 mb-4">
              <div className="bg-dark-700/50 rounded-lg p-3">
                <p className="text-[10px] text-dark-400 mb-1">Total Customers</p>
                <p className="text-lg font-bold text-white">{formatNumber(customers.total)}</p>
              </div>
              <div className="bg-dark-700/50 rounded-lg p-3">
                <p className="text-[10px] text-dark-400 mb-1">New (30d)</p>
                <p className="text-lg font-bold text-primary-400">{formatNumber(customers.new)}</p>
              </div>
              <div className="bg-dark-700/50 rounded-lg p-3">
                <p className="text-[10px] text-dark-400 mb-1">Returning</p>
                <p className="text-lg font-bold text-emerald-400">{formatNumber(customers.returning)}</p>
              </div>
              <div className="bg-dark-700/50 rounded-lg p-3">
                <p className="text-[10px] text-dark-400 mb-1">Avg Customer Value</p>
                <p className="text-lg font-bold text-cyan-400">₹{formatNumber(customers.avg_customer_value)}</p>
              </div>
            </div>
            <div className="flex items-center justify-between text-xs text-dark-300 mb-3">
              <span>Repeat purchase rate</span>
              <span className="font-bold text-emerald-400">{customers.repeat_purchase_rate}%</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {customers.segments.map((seg, i) => (
                <span key={i} className="badge-info text-[10px] px-2 py-1">{seg.name}: {formatNumber(seg.count)}</span>
              ))}
            </div>
          </div>

          <div className="card p-5">
            <h3 className="text-sm font-semibold text-white mb-4">🎯 Conversion Funnel</h3>
            {funnel.length > 0 ? (
              <div className="space-y-3">
                {funnel.map((f, i) => (
                  <div key={i}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-dark-300">{f.stage}</span>
                      <span className="text-dark-200 font-medium">{formatNumber(f.count)}</span>
                    </div>
                    <div className="w-full bg-dark-700 rounded-full h-2 overflow-hidden">
                      <div
                        className={`h-2 rounded-full ${i === funnel.length - 1 ? 'bg-emerald-500' : 'bg-gradient-to-r from-primary-600 to-primary-400'}`}
                        style={{ width: `${Math.max((f.count / (funnel[0]?.count || 1)) * 100, 3)}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-[10px] text-dark-500 mt-0.5">
                      <span>{i === 0 ? 'Baseline' : `${f.pct}% of previous stage`}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-dark-400 text-center py-6">No funnel data available.</p>
            )}
          </div>
        </div>
      )}

      {/* Growth Insights */}
      {data.growth_insights && data.growth_insights.length > 0 && (
        <div className="card p-5 mb-6">
          <h3 className="text-sm font-semibold text-white mb-4">💡 Growth Insights</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {data.growth_insights.map((insight, i) => (
              <div key={i} className="flex items-start gap-2 p-2.5 bg-dark-700/40 rounded-lg">
                <span className="text-emerald-400 text-xs mt-0.5">◆</span>
                <p className="text-xs text-dark-200">{insight}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Growth Opportunities */}
      {data.growth_opportunities && data.growth_opportunities.length > 0 && (
        <div className="card p-5 mb-6">
          <h3 className="text-sm font-semibold text-white mb-4">🚀 Growth Opportunities</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {data.growth_opportunities.map((opp, i) => (
              <div key={i} className="bg-dark-700/50 rounded-lg p-4 border border-dark-600">
                <p className="text-sm font-bold text-primary-300 mb-1">{opp.opportunity}</p>
                <p className="text-xs text-emerald-400 mb-1">Expected impact: {opp.impact}</p>
                <p className="text-xs text-dark-300 mb-1">{opp.reason}</p>
                <p className="text-[11px] text-dark-400">{opp.action}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Bottom Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Products */}
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-white mb-4">🏆 Top Products by Revenue</h3>
          {data.top_products && data.top_products.length > 0 ? (
            <div className="space-y-3">
              {data.top_products.map((p, i) => (
                <div key={i} className="flex items-center gap-3 p-2.5 bg-dark-700/50 rounded-lg">
                  <ProductImage src={p.image_url} alt={p.name} />
                  <div className="flex-1 min-w-0">
                    {p.id ? (
                      <a href={`/product?id=${p.id}`} className="text-sm font-medium text-dark-100 truncate hover:text-primary-300 transition-colors block">
                        {sanitizeProductName(p.name)}
                      </a>
                    ) : (
                      <p className="text-sm font-medium text-dark-100 truncate">{sanitizeProductName(p.name)}</p>
                    )}
                    <p className="text-xs text-dark-400">{p.sales} sales · {p.stock} stock{p.price ? ` · ${formatPrice(p.price)}` : ''}</p>
                  </div>
                  <span className="text-sm font-semibold text-emerald-400">₹{formatNumber(p.revenue)}</span>
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
          {data.recent_orders && data.recent_orders.length > 0 ? (
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
                    <p className="text-sm font-semibold text-white">₹{formatNumber(o.total)}</p>
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

        {/* Best Sellers */}
        {data.best_sellers && data.best_sellers.length > 0 && (
          <div className="card p-5">
            <h3 className="text-sm font-semibold text-white mb-4">🚀 Best Sellers</h3>
            <div className="space-y-3">
              {data.best_sellers.map((p, i) => (
                <div key={i} className="flex items-center gap-3 p-2.5 bg-dark-700/50 rounded-lg">
                  <ProductImage src={p.image_url} alt={p.name} />
                  <div className="flex-1 min-w-0">
                    {p.id ? (
                      <a href={`/product?id=${p.id}`} className="text-sm font-medium text-dark-100 truncate hover:text-primary-300 transition-colors block">
                        {sanitizeProductName(p.name)}
                      </a>
                    ) : (
                      <p className="text-sm font-medium text-dark-100 truncate">{sanitizeProductName(p.name)}</p>
                    )}
                    <p className="text-xs text-dark-400">{p.category} · {p.stock} stock</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-emerald-400">{p.sales} sold</p>
                    <p className="text-[10px] text-dark-400">₹{formatNumber(p.revenue)}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Slow Movers */}
        {data.slow_movers && data.slow_movers.length > 0 && (
          <div className="card p-5">
            <h3 className="text-sm font-semibold text-white mb-4">🐢 Slow Movers</h3>
            <div className="space-y-3">
              {data.slow_movers.map((p, i) => (
                <div key={i} className="flex items-center gap-3 p-2.5 bg-dark-700/50 rounded-lg">
                  <ProductImage src={p.image_url} alt={p.name} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-dark-100 truncate">{sanitizeProductName(p.name)}</p>
                    <p className="text-xs text-dark-400">{p.category}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-amber-400">{p.sales} sold</p>
                    <p className="text-[10px] text-dark-400">{p.stock} in stock</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Low Stock */}
        {data.low_stock_list && data.low_stock_list.length > 0 && (
          <div className="card p-5">
            <h3 className="text-sm font-semibold text-white mb-4">⚠️ Low Stock Alert</h3>
            <div className="space-y-3">
              {data.low_stock_list.slice(0, 6).map((p, i) => (
                <div key={i} className="flex items-center gap-3 p-2.5 bg-dark-700/50 rounded-lg">
                  <ProductImage src={p.image_url} alt={p.name} />
                  <div className="flex-1 min-w-0">
                    {p.id ? (
                      <a href={`/product?id=${p.id}`} className="text-sm font-medium text-dark-100 truncate hover:text-primary-300 transition-colors block">
                        {sanitizeProductName(p.name)}
                      </a>
                    ) : (
                      <p className="text-sm font-medium text-dark-100 truncate">{sanitizeProductName(p.name)}</p>
                    )}
                    <p className="text-xs text-dark-400">{p.category} · {p.sales} sold</p>
                  </div>
                  <span className={`text-xs font-medium ${(p.status === 'Critical' || p.stock <= 3) ? 'text-red-400' : 'text-amber-400'}`}>
                    {p.status || (p.stock <= 3 ? 'Critical' : 'Low')} · {p.stock} left
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Category Revenue */}
        {data.category_revenue && data.category_revenue.length > 0 && (
          <div className="card p-5">
            <h3 className="text-sm font-semibold text-white mb-4">📊 Revenue by Category</h3>
            <div className="space-y-3">
              {data.category_revenue.map((cat, i) => {
                const maxCatRev = Math.max(...data.category_revenue.map(c => c.revenue), 1)
                return (
                  <div key={i}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-dark-300">{cat.category}</span>
                      <span className="text-white font-medium">₹{formatNumber(cat.revenue)}</span>
                    </div>
                    <div className="w-full bg-dark-700 rounded-full h-1.5">
                      <div
                        className="bg-primary-500 h-1.5 rounded-full transition-all"
                        style={{ width: `${Math.max((cat.revenue / maxCatRev) * 100, 2)}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}
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
