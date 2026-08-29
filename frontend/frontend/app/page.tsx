'use client'

import { useEffect, useState } from 'react'

interface Analytics {
  total_orders: number
  total_revenue: number
  average_order_value: number
  upsell_conversions: number
  cross_sell_conversions: number
  payment_success_rate: number
  payment_failure_rate: number
  policy_blocks: number
  total_items_sold: number
  high_value_opportunities: number
}

export default function Dashboard() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAnalytics()
  }, [])

  const fetchAnalytics = async () => {
    try {
      const res = await fetch('/api/analytics/')
      const data = await res.json()
      setAnalytics(data)
    } catch (error) {
      console.error('Failed to fetch analytics')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Merchant Dashboard</h1>
        <p className="text-gray-600 mt-1">TechZone Electronics - Growth Analytics</p>
        <span className="inline-block mt-2 px-2 py-1 bg-yellow-100 text-yellow-800 text-xs font-medium rounded">
          TEST MODE - Simulated Metrics
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          title="Total Orders"
          value={analytics?.total_orders || 0}
          icon="📦"
          color="blue"
        />
        <StatCard
          title="Total Revenue"
          value={`₹${(analytics?.total_revenue || 0).toLocaleString()}`}
          icon="💰"
          color="green"
        />
        <StatCard
          title="Avg Order Value"
          value={`₹${(analytics?.average_order_value || 0).toLocaleString()}`}
          icon="📊"
          color="purple"
        />
        <StatCard
          title="Items Sold"
          value={analytics?.total_items_sold || 0}
          icon="🏷️"
          color="orange"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          title="Upsell Conversions"
          value={analytics?.upsell_conversions || 0}
          icon="📈"
          color="emerald"
          subtitle="Agent recommended"
        />
        <StatCard
          title="Cross-sell Conversions"
          value={analytics?.cross_sell_conversions || 0}
          icon="🔗"
          color="cyan"
          subtitle="Agent recommended"
        />
        <StatCard
          title="Payment Success Rate"
          value={`${analytics?.payment_success_rate || 0}%`}
          icon="✅"
          color="green"
        />
        <StatCard
          title="Policy Blocks"
          value={analytics?.policy_blocks || 0}
          icon="🚫"
          color="red"
          subtitle="Agent prevented"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Agent Activity</h3>
          <div className="space-y-3">
            <ActivityItem
              time="Just now"
              action="Product search executed"
              status="success"
            />
            <ActivityItem
              time="2 min ago"
              action="Cross-sell recommended: Carrying Case"
              status="success"
            />
            <ActivityItem
              time="5 min ago"
              action="Policy check: Transaction within limit"
              status="success"
            />
            <ActivityItem
              time="10 min ago"
              action="Payment approval requested"
              status="pending"
            />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">High-Value Opportunities</h3>
          <div className="space-y-3">
            <OpportunityItem
              product="Mechanical Keyboard + Mouse"
              value="₹4,798"
              probability="High"
            />
            <OpportunityItem
              product="Laptop Stand + Cooling Pad"
              value="₹1,898"
              probability="Medium"
            />
            <OpportunityItem
              product="Webcam + Ring Light"
              value="₹3,098"
              probability="High"
            />
          </div>
        </div>
      </div>
    </div>
  )
}

function StatCard({ title, value, icon, color, subtitle }: {
  title: string
  value: string | number
  icon: string
  color: string
  subtitle?: string
}) {
  const colorClasses: Record<string, string> = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    purple: 'bg-purple-50 text-purple-600',
    orange: 'bg-orange-50 text-orange-600',
    emerald: 'bg-emerald-50 text-emerald-600',
    cyan: 'bg-cyan-50 text-cyan-600',
    red: 'bg-red-50 text-red-600',
  }

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
          {subtitle && (
            <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
          )}
        </div>
        <div className={`p-3 rounded-full ${colorClasses[color] || 'bg-gray-50 text-gray-600'}`}>
          <span className="text-xl">{icon}</span>
        </div>
      </div>
    </div>
  )
}

function ActivityItem({ time, action, status }: {
  time: string
  action: string
  status: string
}) {
  const statusColors: Record<string, string> = {
    success: 'bg-green-500',
    pending: 'bg-yellow-500',
    failed: 'bg-red-500',
  }

  return (
    <div className="flex items-center gap-3">
      <div className={`w-2 h-2 rounded-full ${statusColors[status] || 'bg-gray-500'}`}></div>
      <div className="flex-1">
        <p className="text-sm text-gray-900">{action}</p>
        <p className="text-xs text-gray-500">{time}</p>
      </div>
    </div>
  )
}

function OpportunityItem({ product, value, probability }: {
  product: string
  value: string
  probability: string
}) {
  const probColors: Record<string, string> = {
    High: 'bg-green-100 text-green-800',
    Medium: 'bg-yellow-100 text-yellow-800',
    Low: 'bg-red-100 text-red-800',
  }

  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
      <div>
        <p className="text-sm font-medium text-gray-900">{product}</p>
        <p className="text-lg font-bold text-primary-600">{value}</p>
      </div>
      <span className={`px-2 py-1 text-xs font-medium rounded ${probColors[probability]}`}>
        {probability}
      </span>
    </div>
  )
}
