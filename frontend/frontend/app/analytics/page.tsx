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

export default function AnalyticsPage() {
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
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Growth Analytics</h1>
        <p className="text-gray-600 mt-1">AI-powered revenue insights</p>
        <span className="inline-block mt-2 px-2 py-1 bg-yellow-100 text-yellow-800 text-xs font-medium rounded">
          TEST MODE - Simulated Metrics
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Revenue Metrics</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
              <span className="text-gray-600">Total Revenue</span>
              <span className="text-2xl font-bold text-green-600">
                ₹{(analytics?.total_revenue || 0).toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
              <span className="text-gray-600">Average Order Value</span>
              <span className="text-xl font-bold text-primary-600">
                ₹{(analytics?.average_order_value || 0).toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
              <span className="text-gray-600">Total Orders</span>
              <span className="text-xl font-bold text-gray-900">
                {analytics?.total_orders || 0}
              </span>
            </div>
            <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
              <span className="text-gray-600">Items Sold</span>
              <span className="text-xl font-bold text-gray-900">
                {analytics?.total_items_sold || 0}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">AI Agent Performance</h3>
          <div className="space-y-4">
            <div className="p-3 bg-blue-50 rounded">
              <div className="flex justify-between items-center mb-2">
                <span className="text-blue-800 font-medium">Upsell Conversions</span>
                <span className="text-xl font-bold text-blue-600">
                  {analytics?.upsell_conversions || 0}
                </span>
              </div>
              <p className="text-xs text-blue-600">Agent recommended upsells accepted</p>
            </div>
            <div className="p-3 bg-purple-50 rounded">
              <div className="flex justify-between items-center mb-2">
                <span className="text-purple-800 font-medium">Cross-sell Conversions</span>
                <span className="text-xl font-bold text-purple-600">
                  {analytics?.cross_sell_conversions || 0}
                </span>
              </div>
              <p className="text-xs text-purple-600">Agent recommended cross-sells accepted</p>
            </div>
            <div className="p-3 bg-green-50 rounded">
              <div className="flex justify-between items-center mb-2">
                <span className="text-green-800 font-medium">Revenue Opportunity</span>
                <span className="text-xl font-bold text-green-600">
                  ₹{((analytics?.upsell_conversions || 0) * 500 + (analytics?.cross_sell_conversions || 0) * 300).toLocaleString()}
                </span>
              </div>
              <p className="text-xs text-green-600">Additional revenue from recommendations</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Payment Metrics</h3>
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <div className="flex justify-between text-sm mb-1">
                  <span>Success Rate</span>
                  <span className="font-semibold">{analytics?.payment_success_rate || 0}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-green-500 h-2 rounded-full"
                    style={{ width: `${analytics?.payment_success_rate || 0}%` }}
                  ></div>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <div className="flex justify-between text-sm mb-1">
                  <span>Failure Rate</span>
                  <span className="font-semibold">{analytics?.payment_failure_rate || 0}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-red-500 h-2 rounded-full"
                    style={{ width: `${analytics?.payment_failure_rate || 0}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Safety Metrics</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center p-3 bg-red-50 rounded">
              <span className="text-red-800">Policy Blocks</span>
              <span className="text-xl font-bold text-red-600">
                {analytics?.policy_blocks || 0}
              </span>
            </div>
            <div className="flex justify-between items-center p-3 bg-yellow-50 rounded">
              <span className="text-yellow-800">High-Value Opportunities</span>
              <span className="text-xl font-bold text-yellow-600">
                {analytics?.high_value_opportunities || 0}
              </span>
            </div>
            <div className="p-3 bg-gray-50 rounded text-sm text-gray-600">
              <p className="font-medium mb-1">Agent Bounded Actions:</p>
              <ul className="list-disc list-inside space-y-1">
                <li>Cannot exceed spending limits</li>
                <li>Requires explicit approval</li>
                <li>Cannot invent product prices</li>
                <li>All actions are audited</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
