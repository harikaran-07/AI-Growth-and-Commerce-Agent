'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState, useEffect } from 'react'

const navItems = [
  { href: '/', label: 'Dashboard', icon: '📊', color: 'text-blue-400' },
  { href: '/buyer', label: 'Commerce Assistant', icon: '💬', color: 'text-purple-400' },
  { href: '/products', label: 'Products', icon: '📦', color: 'text-cyan-400' },
  { href: '/cart', label: 'Cart', icon: '🛒', color: 'text-amber-400' },
  { href: '/orders', label: 'Orders', icon: '📋', color: 'text-emerald-400' },
  { href: '/payments', label: 'Payments', icon: '💳', color: 'text-green-400' },
  { href: '/analytics', label: 'Analytics', icon: '📈', color: 'text-pink-400' },
  { href: '/growth', label: 'Growth & Investment', icon: '🚀', color: 'text-violet-400' },
  { href: '/audit', label: 'Audit Trail', icon: '🔍', color: 'text-orange-400' },
  { href: '/settings', label: 'Settings', icon: '⚙️', color: 'text-gray-400' },
]

export default function Sidebar() {
  const pathname = usePathname()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [notifCount, setNotifCount] = useState(0)

  useEffect(() => {
    fetch('/api/notifications/unread-count')
      .then(r => r.json())
      .then(d => setNotifCount(d.count || 0))
      .catch(() => {})
  }, [])

  // Close mobile menu on navigation
  useEffect(() => {
    setMobileOpen(false)
  }, [pathname])

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="p-4 border-b border-dark-700">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
            <span className="text-white font-bold text-lg">M</span>
          </div>
          <div>
            <h1 className="text-lg font-bold text-white leading-tight">AI Growth</h1>
            <p className="text-[10px] text-dark-400 uppercase tracking-wider">Commerce Agent</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                isActive
                  ? 'bg-primary-600/20 text-primary-300 border border-primary-500/20'
                  : 'text-dark-300 hover:bg-dark-700 hover:text-white border border-transparent'
              }`}
            >
              <span className={`text-base ${isActive ? item.color : 'text-dark-400'}`}>{item.icon}</span>
              <span>{item.label}</span>
              {item.href === '/cart' && (
                <span className="ml-auto bg-amber-500/20 text-amber-400 text-[10px] px-1.5 py-0.5 rounded-full font-bold">
                  {notifCount > 0 ? notifCount : ''}
                </span>
              )}
            </Link>
          )
        })}
      </nav>

      {/* Status */}
      <div className="p-3 border-t border-dark-700">
        <div className="bg-dark-800 rounded-lg p-3 border border-dark-700">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></div>
            <span className="text-xs font-medium text-dark-300">System Active</span>
          </div>
          <p className="text-[10px] text-dark-500">Razorpay TEST MODE</p>
        </div>
      </div>
    </div>
  )

  return (
    <>
      {/* Mobile hamburger */}
      <button
        onClick={() => setMobileOpen(!mobileOpen)}
        className="lg:hidden fixed top-3 left-3 z-50 p-2 rounded-lg bg-dark-800 border border-dark-600 text-dark-200"
        aria-label="Toggle navigation"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          {mobileOpen ? (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          ) : (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          )}
        </svg>
      </button>

      {/* Desktop sidebar */}
      <aside className="hidden lg:flex w-60 bg-dark-900 border-r border-dark-700 flex-col flex-shrink-0">
        <SidebarContent />
      </aside>

      {/* Mobile sidebar overlay */}
      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 z-40">
          <div className="absolute inset-0 bg-black/60" onClick={() => setMobileOpen(false)} />
          <aside className="absolute left-0 top-0 bottom-0 w-64 bg-dark-900 border-r border-dark-700 z-50">
            <SidebarContent />
          </aside>
        </div>
      )}
    </>
  )
}
