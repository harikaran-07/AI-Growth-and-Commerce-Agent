'use client'

import { useEffect, useState } from 'react'

interface AuditLog {
  id: string; session_id: string | null; user: string | null; action: string;
  description: string | null; tool_called: string | null; input_data: string | null;
  decision: string | null; policy_result: string | null; approval_status: string | null;
  payment_reference: string | null; final_status: string | null; event_type: string | null;
  related_entity: string | null; financial_impact: number | null; created_at: string;
}

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedLog, setExpandedLog] = useState<string | null>(null)
  const [eventType, setEventType] = useState('')

  useEffect(() => { fetchLogs() }, [eventType])

  const fetchLogs = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ limit: '100' })
      if (eventType) params.set('event_type', eventType)
      const res = await fetch(`/api/audit/?${params}`)
      if (res.ok) { const data = await res.json(); setLogs(data) }
    } catch (e) { console.error('Failed to fetch audit logs') }
    finally { setLoading(false) }
  }

  const statusColor = (status: string | null) => {
    if (!status) return 'badge-neutral'
    if (status.includes('success') || status.includes('approved')) return 'badge-success'
    if (status.includes('failed') || status.includes('blocked')) return 'badge-danger'
    if (status.includes('pending')) return 'badge-warning'
    return 'badge-neutral'
  }

  const eventTypes = [
    { value: '', label: 'All Events' },
    { value: 'payment', label: '💳 Payments' },
    { value: 'pricing', label: '💰 Pricing' },
    { value: 'inventory', label: '📦 Inventory' },
    { value: 'ai', label: '🤖 AI' },
    { value: 'order', label: '📋 Orders' },
    { value: 'system', label: '⚙️ System' },
  ]

  return (
    <div className="p-6 lg:p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Audit Trail</h1>
          <p className="text-slate-500 text-sm mt-1">Complete log of all system actions</p>
        </div>
        <div className="flex gap-1 flex-wrap">
          {eventTypes.map(et => (
            <button key={et.value} onClick={() => setEventType(et.value)}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                eventType === et.value ? 'bg-primary-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}>
              {et.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => <div key={i} className="h-16 bg-slate-200/70 rounded-lg animate-pulse"></div>)}
        </div>
      ) : logs.length === 0 ? (
        <div className="card p-12 text-center">
          <div className="text-6xl mb-4">🔍</div>
          <p className="text-slate-600 text-lg">No audit logs yet</p>
          <p className="text-slate-400 text-sm mt-1">Interact with the AI assistant or make purchases to generate logs</p>
        </div>
      ) : (
        <div className="space-y-2">
          {logs.map(log => (
            <div key={log.id} className="card overflow-hidden">
              <div className="p-3.5 cursor-pointer hover:bg-slate-50 transition-colors" onClick={() => setExpandedLog(expandedLog === log.id ? null : log.id)}>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-slate-400 font-mono w-16 flex-shrink-0">
                    {new Date(log.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                  <span className="font-medium text-sm text-slate-900 flex-shrink-0">{log.action}</span>
                  {log.tool_called && <span className="badge-info text-[10px]">{log.tool_called}</span>}
                  {log.description && <span className="text-xs text-slate-500 truncate flex-1">{log.description}</span>}
                  <div className="flex items-center gap-2 ml-auto flex-shrink-0">
                    {log.financial_impact && log.financial_impact !== 0 && (
                      <span className="text-xs text-emerald-600">₹{Math.abs(log.financial_impact).toLocaleString()}</span>
                    )}
                    {log.final_status && <span className={statusColor(log.final_status)}>{log.final_status}</span>}
                    <span className="text-slate-400 text-xs">{expandedLog === log.id ? '▼' : '▶'}</span>
                  </div>
                </div>
              </div>
              {expandedLog === log.id && (
                <div className="px-4 pb-4 border-t border-slate-200 bg-slate-50">
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-3 text-xs">
                    <div><p className="text-slate-400 mb-0.5">Event Type</p><p className="text-slate-700">{log.event_type || '-'}</p></div>
                    <div><p className="text-slate-400 mb-0.5">Decision</p><p className="text-slate-700">{log.decision || '-'}</p></div>
                    <div><p className="text-slate-400 mb-0.5">Related Entity</p><p className="text-slate-700 font-mono truncate">{log.related_entity || '-'}</p></div>
                    <div><p className="text-slate-400 mb-0.5">Full Timestamp</p><p className="text-slate-700">{new Date(log.created_at).toLocaleString()}</p></div>
                  </div>
                  {log.input_data && (
                    <div className="mt-3">
                      <p className="text-xs text-slate-400 mb-1">Input Data</p>
                      <pre className="text-xs bg-slate-900 p-2 rounded border border-slate-700 text-slate-300 overflow-auto max-h-24">{log.input_data}</pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
