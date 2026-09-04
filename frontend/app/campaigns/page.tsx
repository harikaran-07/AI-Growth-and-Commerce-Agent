'use client'

import { useCallback, useEffect, useState } from 'react'
import { formatPrice, formatNumber } from '../utils'

interface CampaignResult {
  customers_targeted?: number
  customers_converted?: number
  orders_generated?: number
  revenue_generated?: number
  discount_cost?: number
  estimated_profit?: number
  conversion_uplift?: number
  simulated?: boolean
  [key: string]: any
}

interface Campaign {
  campaign_id: string
  name: string
  objective: string
  target_segment: string
  product_ids: string[]
  discount_percentage: number
  budget_limit: number
  expected_revenue: number
  expected_profit: number
  expected_margin: number
  reason: string
  evidence: string
  status: string
  policy_result: string
  approval_status: string
  failure_reason: string | null
  result: CampaignResult | null
  label: string | null
  created_at: string | null
  executed_at: string | null
}

const STATUS_STYLE: Record<string, string> = {
  pending_approval: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  approved: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  executing: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
  completed: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  failed: 'bg-red-500/15 text-red-400 border-red-500/30',
  rejected: 'bg-red-500/15 text-red-400 border-red-500/30',
  rejected_by_policy: 'bg-red-500/15 text-red-400 border-red-500/30',
}

const STATUS_LABEL: Record<string, string> = {
  pending_approval: '⏳ Pending approval',
  approved: '✅ Approved',
  executing: '⚙️ Executing',
  completed: '🎉 Completed',
  failed: '❌ Failed',
  rejected: '⛔ Rejected',
  rejected_by_policy: '🚫 Blocked by policy',
}

function statusChip(c: Campaign) {
  return (
    <span className={`text-[11px] px-2 py-0.5 rounded border font-medium ${STATUS_STYLE[c.status] || 'bg-dark-700 text-dark-300 border-dark-600'}`}>
      {STATUS_LABEL[c.status] || c.status}
    </span>
  )
}

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  // Manual-proposal form (policy-guard demo)
  const [manualName, setManualName] = useState('20% off top smartphones')
  const [manualDiscount, setManualDiscount] = useState('20')
  const [manualBudget, setManualBudget] = useState('5000')
  const [notice, setNotice] = useState<{ kind: 'ok' | 'warn' | 'err'; text: string } | null>(null)

  const loadCampaigns = useCallback(async () => {
    try {
      const res = await fetch('/api/campaigns')
      if (!res.ok) throw new Error('Failed to load campaigns')
      const data = await res.json()
      setCampaigns(data)
      setError(null)
    } catch (e: any) {
      setError(e.message || 'Unable to load campaigns')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadCampaigns()
  }, [loadCampaigns])

  const apiCall = async (url: string, init?: RequestInit): Promise<any> => {
    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
      ...init,
    })
    const body = await res.json().catch(() => ({}))
    if (!res.ok) {
      const detail = body.detail || (Array.isArray(body.detail) ? body.detail.map((d: any) => d.msg).join(', ') : '')
      throw new Error(typeof detail === 'string' ? detail : 'Request failed')
    }
    return body
  }

  const autoPropose = async () => {
    setBusy(true)
    setNotice(null)
    try {
      const body = await apiCall('/api/campaigns/propose', { method: 'POST', body: '{}' })
      const proposed: Campaign[] = body.proposed || []
      setNotice({
        kind: 'ok',
        text: `✅ Agent analyzed the synthetic dataset and proposed ${proposed.length} data-driven campaign(s). Each requires merchant approval before execution.`,
      })
      await loadCampaigns()
    } catch (e: any) {
      setNotice({ kind: 'err', text: e.message })
    } finally {
      setBusy(false)
    }
  }

  const manualPropose = async () => {
    setBusy(true)
    setNotice(null)
    try {
      const discount = parseFloat(manualDiscount)
      const budget = parseFloat(manualBudget) || 0
      if (!manualName.trim()) throw new Error('Give the campaign a name')
      if (!Number.isFinite(discount) || discount <= 0) throw new Error('Enter a valid discount percentage')
      const body = await apiCall('/api/campaigns/propose', {
        method: 'POST',
        body: JSON.stringify({
          name: manualName.trim(),
          objective: 'Increase conversion',
          target_segment: 'All shoppers',
          discount_percentage: discount,
          budget_limit: budget,
        }),
      })
      const proposed: Campaign[] = body.proposed || []
      const blocked = proposed.find((c) => c.status === 'rejected_by_policy')
      if (blocked) {
        setNotice({
          kind: 'warn',
          text: `🚫 Action blocked by policy. Requested discount: ${discount}% · ${blocked.policy_result || 'Exceeds configured limits.'}`,
        })
      } else {
        setNotice({ kind: 'ok', text: `✅ Campaign "${manualName.trim()}" proposed for merchant approval.` })
      }
      await loadCampaigns()
    } catch (e: any) {
      setNotice({ kind: 'err', text: e.message })
    } finally {
      setBusy(false)
    }
  }

  const act = async (campaign: Campaign, action: 'approve' | 'reject' | 'execute', extra?: Record<string, any>) => {
    setBusy(true)
    setNotice(null)
    try {
      const body = await apiCall(`/api/campaigns/${campaign.campaign_id}/${action}`, {
        method: 'POST',
        body: JSON.stringify(extra || {}),
      })
      if (body.status === 'rejected_by_policy') {
        setNotice({ kind: 'warn', text: `🚫 ${body.policy_result || 'Blocked by policy'}` })
      } else if (action === 'execute' && body.status === 'failed') {
        setNotice({ kind: 'err', text: `❌ ${body.failure_reason || 'Campaign execution failed'}` })
      } else {
        setNotice({
          kind: 'ok',
          text: action === 'approve' ? `✅ "${campaign.name}" approved — ready to execute.`
            : action === 'reject' ? `⛔ "${campaign.name}" rejected.`
            : `⚙️ "${campaign.name}" executed (Synthetic Demo Result).`,
        })
      }
      await loadCampaigns()
    } catch (e: any) {
      setNotice({ kind: 'err', text: e.message })
    } finally {
      setBusy(false)
    }
  }

  const canApprove = (c: Campaign) => c.status === 'pending_approval'
  const canExecute = (c: Campaign) => c.status === 'approved'
  const pendingCount = campaigns.filter((c) => c.status === 'pending_approval').length
  const completedCount = campaigns.filter((c) => c.status === 'completed').length
  const blockedCount = campaigns.filter((c) => c.status === 'rejected_by_policy').length

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold text-white">📣 Campaign Orchestrator</h1>
          <p className="text-sm text-dark-400 mt-1">
            Data-driven campaign proposals → policy check → merchant approval → synthetic execution. Every stage is audited.
          </p>
        </div>
        <div className="flex gap-2 text-xs">
          <span className="px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 font-medium">
            ⏳ {pendingCount} awaiting approval
          </span>
          <span className="px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-medium">
            🎉 {completedCount} completed
          </span>
          <span className="px-3 py-1.5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 font-medium">
            🚫 {blockedCount} blocked
          </span>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-300 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={loadCampaigns} className="px-3 py-1 rounded bg-red-500/20 hover:bg-red-500/30 text-red-200 text-xs font-medium">
            Retry
          </button>
        </div>
      )}

      {notice && (
        <div className={`p-3 rounded-lg border text-sm ${
          notice.kind === 'ok' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
          : notice.kind === 'warn' ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
          : 'bg-red-500/10 border-red-500/30 text-red-300'
        }`}>
          {notice.text}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Auto-detect opportunities */}
        <div className="bg-dark-800 border border-dark-700 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-white mb-1">🤖 Auto-detect opportunities</h2>
          <p className="text-xs text-dark-400 mb-4 leading-relaxed">
            The engine analyzes the synthetic merchant dataset (best sellers, category revenue, customer segments,
            inventory, margins) and proposes campaigns with expected impact — never random recommendations.
          </p>
          <button
            onClick={autoPropose}
            disabled={busy}
            className="w-full py-2.5 rounded-lg bg-gradient-to-r from-primary-600 to-violet-600 hover:from-primary-500 hover:to-violet-500 disabled:opacity-50 text-white text-sm font-medium transition-colors"
          >
            {busy ? 'Analyzing dataset...' : '🔍 Analyze & propose campaigns'}
          </button>
          <p className="text-[11px] text-dark-500 mt-3">
            Proposals start as <span className="text-amber-400">pending approval</span> — nothing executes automatically.
          </p>
        </div>

        {/* Manual proposal / policy guard */}
        <div className="bg-dark-800 border border-dark-700 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-white mb-1">🛡️ Policy-guard test</h2>
          <p className="text-xs text-dark-400 mb-4 leading-relaxed">
            Try a discount above the configured limit (max {`10%`} by default) and watch the money-action boundary reject it.
          </p>
          <div className="space-y-3">
            <input
              value={manualName}
              onChange={(e) => setManualName(e.target.value)}
              placeholder="Campaign name"
              className="w-full px-3 py-2 rounded-lg bg-dark-700 border border-dark-600 text-sm text-white placeholder-dark-500 focus:outline-none focus:border-primary-500"
            />
            <div className="grid grid-cols-2 gap-3">
              <input
                value={manualDiscount}
                onChange={(e) => setManualDiscount(e.target.value)}
                type="number"
                min={0}
                max={100}
                placeholder="Discount %"
                className="w-full px-3 py-2 rounded-lg bg-dark-700 border border-dark-600 text-sm text-white placeholder-dark-500 focus:outline-none focus:border-primary-500"
              />
              <input
                value={manualBudget}
                onChange={(e) => setManualBudget(e.target.value)}
                type="number"
                min={0}
                placeholder="Budget ₹"
                className="w-full px-3 py-2 rounded-lg bg-dark-700 border border-dark-600 text-sm text-white placeholder-dark-500 focus:outline-none focus:border-primary-500"
              />
            </div>
            <button
              onClick={manualPropose}
              disabled={busy}
              className="w-full py-2.5 rounded-lg bg-dark-600 hover:bg-dark-500 disabled:opacity-50 text-white text-sm font-medium transition-colors border border-dark-500"
            >
              {busy ? 'Checking policy...' : 'Propose campaign (policy check)'}
            </button>
          </div>
        </div>
      </div>

      {/* Campaign list */}
      <div className="bg-dark-800 border border-dark-700 rounded-xl">
        <div className="px-5 py-4 border-b border-dark-700 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-white">Campaigns & approvals</h2>
          <button onClick={loadCampaigns} className="text-xs text-dark-400 hover:text-white transition-colors">↻ Refresh</button>
        </div>
        {loading ? (
          <div className="p-10 text-center text-sm text-dark-400">Loading campaigns...</div>
        ) : campaigns.length === 0 ? (
          <div className="p-10 text-center">
            <p className="text-sm text-dark-400">No campaigns yet. Use <span className="text-white">Analyze &amp; propose campaigns</span> to start.</p>
          </div>
        ) : (
          <div className="divide-y divide-dark-700">
            {campaigns.map((c) => (
              <div key={c.campaign_id} className="px-5 py-4">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center gap-3 flex-wrap">
                    <span className="text-sm font-semibold text-white">{c.name}</span>
                    {statusChip(c)}
                    {c.label === 'synthetic' && (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-purple-500/15 text-purple-300 border border-purple-500/30">
                        Synthetic Demo Result
                      </span>
                    )}
                  </div>
                  <div className="flex gap-2">
                    {canApprove(c) && (
                      <>
                        <button
                          onClick={() => act(c, 'approve')}
                          disabled={busy}
                          className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-medium"
                        >
                          ✓ Approve
                        </button>
                        <button
                          onClick={() => act(c, 'reject')}
                          disabled={busy}
                          className="px-3 py-1.5 rounded-lg bg-red-600/80 hover:bg-red-500 disabled:opacity-50 text-white text-xs font-medium"
                        >
                          ✕ Reject
                        </button>
                      </>
                    )}
                    {canExecute(c) && (
                      <>
                        <button
                          onClick={() => act(c, 'execute')}
                          disabled={busy}
                          className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-medium"
                        >
                          ⚙️ Execute
                        </button>
                        <button
                          onClick={() => act(c, 'execute', { simulate_inventory_failure: true })}
                          disabled={busy}
                          title="Demonstrates graceful campaign failure"
                          className="px-3 py-1.5 rounded-lg bg-dark-600 hover:bg-dark-500 disabled:opacity-50 text-dark-200 text-xs font-medium border border-dark-500"
                        >
                          💥 Simulate failure
                        </button>
                      </>
                    )}
                  </div>
                </div>

                <div className="mt-2 grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                  <div className="text-dark-400"><span className="text-dark-500">Objective:</span> <span className="text-dark-200">{c.objective}</span></div>
                  <div className="text-dark-400"><span className="text-dark-500">Target:</span> <span className="text-dark-200">{c.target_segment}</span></div>
                  <div className="text-dark-400"><span className="text-dark-500">Discount:</span> <span className="text-dark-200">{c.discount_percentage}%</span></div>
                  <div className="text-dark-400"><span className="text-dark-500">Budget:</span> <span className="text-dark-200">{formatPrice(c.budget_limit)}</span></div>
                </div>

                <p className="mt-2 text-xs text-dark-300 leading-relaxed"><span className="text-dark-500">Why:</span> {c.reason}</p>
                {c.evidence && (
                  <p className="mt-1 text-[11px] text-dark-500 leading-relaxed"><span className="text-dark-600">Evidence:</span> {c.evidence}</p>
                )}

                <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-dark-400">
                  <span>Expected revenue: <span className="text-emerald-400 font-medium">{formatPrice(c.expected_revenue)}</span></span>
                  <span>Expected profit: <span className="text-emerald-400 font-medium">{formatPrice(c.expected_profit)}</span></span>
                  <span>Expected margin: <span className="text-emerald-400 font-medium">{c.expected_margin}%</span></span>
                </div>

                {c.status === 'rejected_by_policy' && c.policy_result && (
                  <p className="mt-2 text-[11px] px-2.5 py-1.5 rounded bg-red-500/10 border border-red-500/25 text-red-300">
                    🚫 {c.policy_result}
                  </p>
                )}
                {c.status === 'failed' && c.failure_reason && (
                  <p className="mt-2 text-[11px] px-2.5 py-1.5 rounded bg-red-500/10 border border-red-500/25 text-red-300">
                    ❌ {c.failure_reason}
                  </p>
                )}

                {c.result && (c.status === 'completed' || c.status === 'failed') && (
                  <div className="mt-3 p-3 rounded-lg bg-dark-700/50 border border-dark-600">
                    <p className="text-[10px] uppercase tracking-wider text-purple-400 mb-2">Synthetic Demo Result</p>
                    {c.status === 'completed' && (
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs">
                        <div className="text-dark-400">Customers targeted <span className="block text-white font-semibold">{formatNumber(c.result.customers_targeted || 0)}</span></div>
                        <div className="text-dark-400">Customers converted <span className="block text-white font-semibold">{formatNumber(c.result.customers_converted || 0)}</span></div>
                        <div className="text-dark-400">Orders generated <span className="block text-white font-semibold">{formatNumber(c.result.orders_generated || 0)}</span></div>
                        <div className="text-dark-400">Revenue generated <span className="block text-emerald-400 font-semibold">{formatPrice(c.result.revenue_generated || 0)}</span></div>
                        <div className="text-dark-400">Discount cost <span className="block text-amber-400 font-semibold">{formatPrice(c.result.discount_cost || 0)}</span></div>
                        <div className="text-dark-400">Estimated profit <span className="block text-emerald-400 font-semibold">{formatPrice(c.result.estimated_profit || 0)}</span></div>
                        {typeof c.result.conversion_uplift === 'number' && (
                          <div className="text-dark-400">Conversion uplift <span className="block text-emerald-400 font-semibold">+{c.result.conversion_uplift}%</span></div>
                        )}
                      </div>
                    )}
                    {c.status === 'failed' && (
                      <p className="text-xs text-red-300">Execution failed — no inventory or payment records were changed. See the audit trail for the failure event.</p>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
