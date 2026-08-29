'use client'

import { useEffect, useState } from 'react'

interface Policy {
  id: string
  max_transaction_amount: number
  max_discount_percentage: number
  payment_requires_approval: boolean
  max_retry_attempts: number
}

export default function SettingsPage() {
  const [policy, setPolicy] = useState<Policy | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    fetchPolicy()
  }, [])

  const fetchPolicy = async () => {
    try {
      const res = await fetch('/api/policies/')
      const data = await res.json()
      setPolicy(data)
    } catch (error) {
      console.error('Failed to fetch policy')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!policy) return
    setSaving(true)
    try {
      const res = await fetch('/api/policies/', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(policy)
      })
      if (res.ok) {
        setMessage('Policy updated successfully!')
        setTimeout(() => setMessage(''), 3000)
      }
    } catch (error) {
      setMessage('Failed to update policy')
    } finally {
      setSaving(false)
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
        <h1 className="text-2xl font-bold text-gray-900">Agent Policies</h1>
        <p className="text-gray-600 mt-1">Configure spending limits and approval requirements</p>
      </div>

      <div className="max-w-2xl">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-6">Spending Policies</h2>

          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Maximum Transaction Amount (₹)
              </label>
              <input
                type="number"
                value={policy?.max_transaction_amount || 3000}
                onChange={(e) => setPolicy(prev => prev ? {
                  ...prev,
                  max_transaction_amount: parseFloat(e.target.value)
                } : null)}
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                Transactions above this amount will be blocked by the policy engine
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Maximum Discount Percentage
              </label>
              <input
                type="number"
                value={policy?.max_discount_percentage || 10}
                onChange={(e) => setPolicy(prev => prev ? {
                  ...prev,
                  max_discount_percentage: parseFloat(e.target.value)
                } : null)}
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                Maximum discount the agent can apply
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Maximum Retry Attempts
              </label>
              <input
                type="number"
                value={policy?.max_retry_attempts || 1}
                onChange={(e) => setPolicy(prev => prev ? {
                  ...prev,
                  max_retry_attempts: parseInt(e.target.value)
                } : null)}
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                How many times the agent can retry a failed payment
              </p>
            </div>

            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <p className="font-medium text-gray-900">Payment Requires Approval</p>
                <p className="text-sm text-gray-600">
                  Require explicit user approval before processing payments
                </p>
              </div>
              <button
                onClick={() => setPolicy(prev => prev ? {
                  ...prev,
                  payment_requires_approval: !prev.payment_requires_approval
                } : null)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  policy?.payment_requires_approval ? 'bg-primary-600' : 'bg-gray-300'
                }`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  policy?.payment_requires_approval ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>
          </div>

          {message && (
            <div className={`mt-4 p-3 rounded ${
              message.includes('success') ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
            }`}>
              {message}
            </div>
          )}

          <div className="mt-6 flex justify-end">
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>

        <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <span className="text-yellow-600 text-xl">⚠️</span>
            <div>
              <h3 className="font-medium text-yellow-800">Safety Notice</h3>
              <p className="text-sm text-yellow-700 mt-1">
                The AI agent cannot override these policies. All financial operations are
                bounded by these limits and require explicit approval when enabled.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
