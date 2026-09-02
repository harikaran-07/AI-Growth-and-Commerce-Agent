'use client'

import { useEffect, useState } from 'react'
import { sanitizeProductName, formatPrice, formatNumber } from '../utils'

interface GrowthData {
  source: string
  label: string
  disclaimer: string
  summary: {
    total_revenue: number
    total_profit: number
    total_orders: number
    total_units_sold: number
    avg_margin: number
    avg_order_value: number
    revenue_growth: number
    profit_growth: number
  }
  monthly_data: { month: string; revenue: number; profit: number; margin: number; orders: number; units_sold: number }[]
  category_performance: { category: string; revenue: number; units_sold: number; product_count: number; avg_margin: number }[]
  growth_score: { score: number; factors: { name: string; impact: string; value: string; weight: number }[]; summary: string }
  investment_recommendations: { type: string; icon: string; title: string; category: string; reason: string; expected_impact: string; confidence: string }[]
  growth_opportunities: { type: string; icon: string; title: string; message: string; metric?: string }[]
  whats_going_well: string[]
  recommended_actions: { action: string; category: string; reason: string }[]
  investment_allocation: { total_budget: number; label: string; disclaimer: string; allocations: { category: string; amount: number; percentage: number; reason: string }[] }
}

export default function GrowthPage() {
  const [data, setData] = useState<GrowthData | null>(null)
  const [loading, setLoading] = useState(true)
  const [mode, setMode] = useState<'synthetic' | 'real'>('synthetic')

  useEffect(() => { fetchData() }, [mode])

  const fetchData = async () => {
    setLoading(true)
    try {
      if (mode === 'synthetic') {
        const res = await fetch('/api/synthetic/dashboard')
        const d = await res.json()
        setData(d)
      } else {
        const res = await fetch('/api/analytics/dashboard')
        const d = await res.json()
        // Map real data to synthetic format
        setData({
          source: 'real',
          label: 'Real Data — Live Transactions',
          disclaimer: 'This data is based on actual orders and payments.',
          summary: {
            total_revenue: d.total_revenue || 0,
            total_profit: d.profit || 0,
            total_orders: d.total_orders || 0,
            total_units_sold: d.products_sold || 0,
            avg_margin: d.margin || 0,
            avg_order_value: d.average_order_value || 0,
            revenue_growth: 0,
            profit_growth: 0,
          },
          monthly_data: [],
          category_performance: d.category_revenue?.map((c: any) => ({
            category: c.category, revenue: c.revenue, units_sold: c.sales, product_count: 0, avg_margin: 0
          })) || [],
          growth_score: { score: 0, factors: [], summary: 'Not enough data for growth score. Complete more orders to enable analysis.' },
          investment_recommendations: [],
          growth_opportunities: [],
          whats_going_well: d.total_orders > 0 ? [`${d.total_orders} orders completed`] : ['No orders yet'],
          recommended_actions: [],
          investment_allocation: { total_budget: 0, label: '', disclaimer: '', allocations: [] },
        })
      }
    } catch (e) { console.error('Failed to fetch growth data') }
    finally { setLoading(false) }
  }

  if (loading) {
    return (
      <div className="p-6 lg:p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-dark-700 rounded w-1/4"></div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[...Array(8)].map((_, i) => <div key={i} className="h-28 bg-dark-800 rounded-lg border border-dark-700"></div>)}
          </div>
        </div>
      </div>
    )
  }

  if (!data) return <div className="p-8 text-dark-400">Failed to load data</div>

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Growth & Investment</h1>
          <p className="text-dark-400 mt-1 text-sm">Business growth analysis and investment recommendations</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex bg-dark-700 rounded-lg p-0.5">
            <button onClick={() => setMode('real')} className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${mode === 'real' ? 'bg-primary-600 text-white' : 'text-dark-300 hover:text-white'}`}>
              Real Data
            </button>
            <button onClick={() => setMode('synthetic')} className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${mode === 'synthetic' ? 'bg-primary-600 text-white' : 'text-dark-300 hover:text-white'}`}>
              Demo Data
            </button>
          </div>
        </div>
      </div>

      {/* Data Source Label */}
      <div className={`mb-6 p-3 rounded-lg border text-sm ${data.source === 'synthetic' ? 'bg-amber-500/5 border-amber-500/20 text-amber-300' : 'bg-emerald-500/5 border-emerald-500/20 text-emerald-300'}`}>
        <span className="font-medium">{data.label}</span>
        <span className="text-dark-400 ml-2">— {data.disclaimer}</span>
      </div>

      {/* AI Growth Score */}
      {data.growth_score.score > 0 && (
        <div className="card p-6 mb-6">
          <div className="flex items-center gap-6">
            <div className="relative">
              <svg className="w-24 h-24" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="40" fill="none" stroke="#1e293b" strokeWidth="8" />
                <circle cx="50" cy="50" r="40" fill="none" stroke={data.growth_score.score >= 70 ? '#10b981' : data.growth_score.score >= 50 ? '#f59e0b' : '#ef4444'} strokeWidth="8" strokeDasharray={`${data.growth_score.score * 2.51} 251`} strokeLinecap="round" transform="rotate(-90 50 50)" />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-2xl font-bold text-white">{data.growth_score.score}</span>
              </div>
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-bold text-white mb-1">Growth Score: {data.growth_score.score}/100</h3>
              <p className="text-sm text-dark-300 mb-3">{data.growth_score.summary}</p>
              <div className="flex flex-wrap gap-2">
                {data.growth_score.factors.map((f, i) => (
                  <span key={i} className={`text-xs px-2 py-1 rounded ${
                    f.impact === 'positive' ? 'bg-emerald-500/10 text-emerald-400' :
                    f.impact === 'negative' ? 'bg-red-500/10 text-red-400' :
                    'bg-dark-600 text-dark-300'
                  }`}>
                    {f.name}: {f.value}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Key Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <MetricCard title="Total Revenue" value={`₹${formatNumber(data.summary.total_revenue)}`} icon="💰" trend={data.summary.revenue_growth ? `${data.summary.revenue_growth > 0 ? '+' : ''}${data.summary.revenue_growth.toFixed(1)}% growth` : 'N/A'} trendUp={data.summary.revenue_growth > 0} color="emerald" />
        <MetricCard title="Total Profit" value={`₹${formatNumber(data.summary.total_profit)}`} icon="📈" trend={`${data.summary.avg_margin.toFixed(1)}% margin`} color="amber" />
        <MetricCard title="Total Orders" value={formatNumber(data.summary.total_orders)} icon="📦" trend={`${formatNumber(data.summary.total_units_sold)} units sold`} color="blue" />
        <MetricCard title="Avg Order Value" value={`₹${formatNumber(data.summary.avg_order_value)}`} icon="📊" trend="Per order" color="purple" />
      </div>

      {/* What's Going Well + Recommended Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-white mb-4">✅ What is Going Well</h3>
          <div className="space-y-3">
            {data.whats_going_well.map((item, i) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-emerald-500/5 border border-emerald-500/10 rounded-lg">
                <span className="text-emerald-400 mt-0.5">✓</span>
                <p className="text-sm text-dark-200">{item}</p>
              </div>
            ))}
          </div>
        </div>
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-white mb-4">🎯 Recommended Next Actions</h3>
          <div className="space-y-3">
            {data.recommended_actions.map((action, i) => (
              <div key={i} className="flex items-center gap-3 p-3 bg-dark-700/50 rounded-lg">
                <span className="text-primary-400 font-bold text-sm">{i + 1}.</span>
                <div className="flex-1">
                  <p className="text-sm text-white">{action.action}</p>
                  <p className="text-xs text-dark-400">{action.reason}</p>
                </div>
                <span className="badge-info text-[10px]">{action.category}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Growth Opportunities */}
      <div className="card p-5 mb-6">
        <h3 className="text-sm font-semibold text-white mb-4">Growth Opportunities</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.growth_opportunities.map((opp, i) => (
            <div key={i} className="bg-dark-700/50 rounded-lg p-4 border border-dark-600">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-lg">{opp.icon}</span>
                <span className="text-sm font-semibold text-white">{opp.title}</span>
              </div>
              <p className="text-xs text-dark-300 mb-2">{opp.message}</p>
              {opp.metric && <span className="text-xs font-bold text-primary-400">{opp.metric}</span>}
            </div>
          ))}
        </div>
      </div>

      {/* Investment Recommendations */}
      {data.investment_recommendations.length > 0 && (
        <div className="card p-5 mb-6">
          <h3 className="text-sm font-semibold text-white mb-4">Investment Recommendations</h3>
          <div className="space-y-4">
            {data.investment_recommendations.map((rec, i) => (
              <div key={i} className="bg-dark-700/50 rounded-lg p-4 border border-dark-600">
                <div className="flex items-start gap-3">
                  <span className="text-2xl">{rec.icon}</span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="text-sm font-bold text-white">{rec.title}</h4>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded ${rec.confidence === 'High' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'}`}>
                        {rec.confidence} Confidence
                      </span>
                    </div>
                    <p className="text-xs text-dark-300 mb-1"><span className="text-dark-400">Reason:</span> {rec.reason}</p>
                    <p className="text-xs text-dark-300"><span className="text-dark-400">Expected impact:</span> {rec.expected_impact}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Investment Allocation */}
      {data.investment_allocation.allocations.length > 0 && (
        <div className="card p-5 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white">Suggested Investment Allocation</h3>
            <span className="text-xs font-bold text-primary-400">Budget: ₹{formatNumber(data.investment_allocation.total_budget)}</span>
          </div>
          <p className="text-[10px] text-amber-400 mb-4">⚠️ {data.investment_allocation.disclaimer}</p>
          <div className="space-y-3">
            {data.investment_allocation.allocations.map((alloc, i) => (
              <div key={i}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-dark-300">{alloc.category}</span>
                  <span className="text-white font-medium">₹{formatNumber(alloc.amount)} ({alloc.percentage}%)</span>
                </div>
                <div className="w-full bg-dark-700 rounded-full h-2">
                  <div className="bg-primary-500 h-2 rounded-full transition-all" style={{ width: `${alloc.percentage}%` }} />
                </div>
                <p className="text-[10px] text-dark-500 mt-0.5">{alloc.reason}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Category Performance */}
      {data.category_performance.length > 0 && (
        <div className="card p-5 mb-6">
          <h3 className="text-sm font-semibold text-white mb-4">Category Performance</h3>
          <div className="space-y-3">
            {data.category_performance.map((cat, i) => {
              const maxRev = Math.max(...data.category_performance.map(c => c.revenue), 1)
              return (
                <div key={i}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-dark-300">{cat.category}</span>
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-dark-400">{cat.units_sold} units</span>
                      <span className="text-xs text-emerald-400">{cat.avg_margin}% margin</span>
                      <span className="text-white font-medium">₹{formatNumber(cat.revenue)}</span>
                    </div>
                  </div>
                  <div className="w-full bg-dark-700 rounded-full h-1.5">
                    <div className="bg-primary-500 h-1.5 rounded-full transition-all" style={{ width: `${Math.max((cat.revenue / maxRev) * 100, 2)}%` }} />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Monthly Trend */}
      {data.monthly_data.length > 0 && (
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-white mb-4">Monthly Revenue Trend</h3>
          <div className="flex items-end gap-1 h-48">
            {data.monthly_data.map((m, i) => {
              const maxRev = Math.max(...data.monthly_data.map(d => d.revenue), 1)
              return (
                <div key={i} className="flex-1 flex flex-col items-center gap-1 group relative">
                  <div className="absolute bottom-full mb-2 hidden group-hover:block bg-dark-800 border border-dark-600 rounded px-2 py-1 text-[10px] text-dark-200 whitespace-nowrap z-10">
                    {m.month}: ₹{formatNumber(m.revenue)}
                  </div>
                  <div className="w-full bg-gradient-to-t from-emerald-600 to-emerald-400 rounded-t-sm" style={{ height: `${Math.max((m.revenue / maxRev) * 100, 2)}%`, minHeight: '2px' }} />
                </div>
              )
            })}
          </div>
          <div className="flex justify-between mt-2 text-[10px] text-dark-500">
            <span>{data.monthly_data[0]?.month}</span>
            <span>{data.monthly_data[data.monthly_data.length - 1]?.month}</span>
          </div>
        </div>
      )}
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
  }
  return (
    <div className={`bg-gradient-to-br ${colorMap[color] || colorMap.blue} border rounded-lg p-4`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-dark-400 font-medium">{title}</p>
          <p className="text-xl font-bold text-white mt-1">{value}</p>
          {trend && <p className={`text-[11px] mt-1 ${trendUp ? 'text-emerald-400' : 'text-dark-400'}`}>{trendUp && '↑ '}{trend}</p>}
        </div>
        <span className="text-xl">{icon}</span>
      </div>
    </div>
  )
}
