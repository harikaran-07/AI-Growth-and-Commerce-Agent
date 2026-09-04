'use client'

import { useEffect, useState } from 'react'

interface Policy {
  id: string; max_transaction_amount: number; max_discount_percentage: number;
  payment_requires_approval: boolean; max_retry_attempts: number;
  max_campaign_budget: number; minimum_margin_percentage: number;
}

interface HealthStatus {
  status: string; service: string; chatbot: { type: string; provider: string; mode: string }; razorpay: string; database: string | { status: string; type: string };
}

export default function SettingsPage() {
  const [policy, setPolicy] = useState<Policy | null>(null)
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    Promise.all([
      fetch('/api/policies/').then(r => r.json()),
      fetch('/health').then(r => r.json()),
    ]).then(([p, h]) => { setPolicy(p); setHealth(h) })
    .catch(() => {})
    .finally(() => setLoading(false))
  }, [])

  const handleSave = async () => {
    if (!policy) return
    setSaving(true)
    try {
      const res = await fetch('/api/policies/', {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(policy),
      })
      if (res.ok) {
        setMessage('Settings saved successfully!')
        setTimeout(() => setMessage(''), 3000)
      }
    } catch (e) { setMessage('Failed to save') }
    finally { setSaving(false) }
  }

  if (loading) return (
    <div className="p-6 lg:p-8">
      <div className="animate-pulse space-y-4">
        <div className="h-8 bg-slate-200/70 rounded w-1/4"></div>
        <div className="h-64 bg-slate-200/70 rounded-lg"></div>
      </div>
    </div>
  )

  return (
    <div className="p-6 lg:p-8 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-slate-900 mb-6">Settings</h1>

      {/* System Status */}
      <div className="card p-5 mb-6">
        <h2 className="text-sm font-semibold text-slate-900 mb-4">System Status</h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <StatusBox label="API" value={health?.status || 'Unknown'} ok={health?.status === 'healthy'} />
          <StatusBox label="Commerce Assistant" value={health?.chatbot?.type || 'rule-based'} ok />
          <StatusBox label="Razorpay" value={health?.razorpay || 'demo_mode'} ok={health?.razorpay !== 'not_configured'} />
          <StatusBox label="Database" value={typeof health?.database === 'object' ? health.database.type : (health?.database || 'sqlite')} ok />
        </div>
      </div>

      {/* Merchant Profile */}
      <div className="card p-5 mb-6">
        <h2 className="text-sm font-semibold text-slate-900 mb-4">Merchant Profile</h2>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-slate-500 mb-1 block">Store Name</label>
            <input type="text" defaultValue="AI Growth & Commerce Agent" className="input" disabled />
          </div>
          <div>
            <label className="text-xs text-slate-500 mb-1 block">Email</label>
            <input type="email" defaultValue="admin@techzone.com" className="input" disabled />
          </div>
          <div>
            <label className="text-xs text-slate-500 mb-1 block">Currency</label>
            <input type="text" defaultValue="INR (₹)" className="input" disabled />
          </div>
        </div>
      </div>

      {/* Agent Policies */}
      <div className="card p-5 mb-6">
        <h2 className="text-sm font-semibold text-slate-900 mb-4">Agent Policies</h2>
        <div className="space-y-4">
          <div>
            <label className="text-xs text-slate-500 mb-1 block">Max Transaction Amount (₹)</label>
            <input type="number" value={policy?.max_transaction_amount || 500000}
              onChange={e => setPolicy(p => p ? { ...p, max_transaction_amount: parseFloat(e.target.value) } : null)}
              className="input" />
            <p className="text-[10px] text-slate-400 mt-1">Transactions above this are blocked</p>
          </div>
          <div>
            <label className="text-xs text-slate-500 mb-1 block">Max Discount %</label>
            <input type="number" value={policy?.max_discount_percentage || 10}
              onChange={e => setPolicy(p => p ? { ...p, max_discount_percentage: parseFloat(e.target.value) } : null)}
              className="input" />
          </div>
          <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-200">
            <div>
              <p className="text-sm font-medium text-slate-900">Payment Requires Approval</p>
              <p className="text-xs text-slate-500">Require explicit approval before payments</p>
            </div>
            <button onClick={() => setPolicy(p => p ? { ...p, payment_requires_approval: !p.payment_requires_approval } : null)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                policy?.payment_requires_approval ? 'bg-primary-600' : 'bg-slate-300'
              }`}>
              <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                policy?.payment_requires_approval ? 'translate-x-6' : 'translate-x-1'
              }`} />
            </button>
          </div>
          <div>
            <label className="text-xs text-slate-500 mb-1 block">Max Campaign Budget (₹)</label>
            <input type="number" value={policy?.max_campaign_budget ?? 100000}
              onChange={e => setPolicy(p => p ? { ...p, max_campaign_budget: parseFloat(e.target.value) } : null)}
              className="input" />
            <p className="text-[10px] text-slate-400 mt-1">Campaign proposals above this are blocked by policy</p>
          </div>
          <div>
            <label className="text-xs text-slate-500 mb-1 block">Minimum Margin %</label>
            <input type="number" value={policy?.minimum_margin_percentage ?? 20}
              onChange={e => setPolicy(p => p ? { ...p, minimum_margin_percentage: parseFloat(e.target.value) } : null)}
              className="input" />
            <p className="text-[10px] text-slate-400 mt-1">Campaigns expected to fall below this margin are blocked</p>
          </div>
        </div>

        {message && (
          <div className={`mt-4 p-3 rounded text-sm ${message.includes('success') ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
            {message}
          </div>
        )}

        <div className="mt-4 flex justify-end">
          <button onClick={handleSave} disabled={saving} className="btn-primary">{saving ? 'Saving...' : 'Save Changes'}</button>
        </div>
      </div>

      {/* Safety Notice */}
      <div className="card p-4 border-amber-200 bg-amber-50">
        <div className="flex items-start gap-3">
          <span className="text-amber-600 text-lg">⚠️</span>
          <div>
            <h3 className="font-medium text-amber-700 text-sm">Safety Notice</h3>
            <p className="text-xs text-slate-600 mt-1">The AI agent cannot override these policies. All financial operations are bounded by these limits.</p>
          </div>
        </div>
      </div>
    </div>
  )
}

function StatusBox({ label, value, ok }: { label: string; value: string; ok: boolean }) {
  return (
    <div className="bg-slate-50 rounded-lg p-3 border border-slate-200">
      <p className="text-[10px] text-slate-500 mb-1">{label}</p>
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${ok ? 'bg-emerald-500' : 'bg-amber-500'}`}></div>
        <span className="text-sm text-slate-900 font-medium">{value}</span>
      </div>
    </div>
  )
}
