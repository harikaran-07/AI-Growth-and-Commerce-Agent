'use client'

import { useEffect, useState } from 'react'

interface AuditLog {
  id: string
  session_id: string | null
  user: string | null
  action: string
  tool_called: string | null
  input_data: string | null
  decision: string | null
  policy_result: string | null
  approval_status: string | null
  payment_reference: string | null
  final_status: string | null
  created_at: string
}

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedLog, setExpandedLog] = useState<string | null>(null)

  useEffect(() => {
    fetchLogs()
  }, [])

  const fetchLogs = async () => {
    try {
      const res = await fetch('/api/audit/')
      if (res.ok) {
        const data = await res.json()
        setLogs(data)
      }
    } catch (error) {
      console.error('Failed to fetch audit logs')
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string | null) => {
    if (!status) return 'bg-gray-100 text-gray-800'
    if (status.includes('success') || status.includes('approved')) return 'bg-green-100 text-green-800'
    if (status.includes('failed') || status.includes('blocked')) return 'bg-red-100 text-red-800'
    if (status.includes('pending')) return 'bg-yellow-100 text-yellow-800'
    return 'bg-gray-100 text-gray-800'
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
        <h1 className="text-2xl font-bold text-gray-900">Agent Audit Trail</h1>
        <p className="text-gray-600 mt-1">Complete log of all agent actions</p>
      </div>

      {logs.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <div className="text-6xl mb-4">📋</div>
          <p className="text-gray-600">No audit logs yet</p>
          <p className="text-sm text-gray-500 mt-2">Start a conversation with the AI buyer to generate logs</p>
        </div>
      ) : (
        <div className="space-y-3">
          {logs.map((log) => (
            <div
              key={log.id}
              className="bg-white rounded-lg shadow overflow-hidden"
            >
              <div
                className="p-4 cursor-pointer hover:bg-gray-50"
                onClick={() => setExpandedLog(expandedLog === log.id ? null : log.id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <span className="text-sm text-gray-500 font-mono">
                      {new Date(log.created_at).toLocaleTimeString()}
                    </span>
                    <span className="font-medium text-gray-900">{log.action}</span>
                    {log.tool_called && (
                      <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                        {log.tool_called}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    {log.final_status && (
                      <span className={`px-2 py-1 text-xs rounded ${getStatusColor(log.final_status)}`}>
                        {log.final_status}
                      </span>
                    )}
                    <span className="text-gray-400">{expandedLog === log.id ? '▼' : '▶'}</span>
                  </div>
                </div>
              </div>

              {expandedLog === log.id && (
                <div className="px-4 pb-4 border-t bg-gray-50">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                    <div>
                      <p className="text-xs text-gray-500">Session ID</p>
                      <p className="text-sm font-mono">{log.session_id || '-'}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">User</p>
                      <p className="text-sm">{log.user || '-'}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Decision</p>
                      <p className="text-sm">{log.decision || '-'}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Final Status</p>
                      <p className="text-sm">{log.final_status || '-'}</p>
                    </div>
                  </div>
                  {log.input_data && (
                    <div className="mt-4">
                      <p className="text-xs text-gray-500 mb-1">Input Data</p>
                      <pre className="text-xs bg-white p-2 rounded border overflow-auto max-h-32">
                        {log.input_data}
                      </pre>
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
