'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const navItems = [
  { href: '/', label: 'Dashboard', icon: '📊' },
  { href: '/buyer', label: 'AI Buyer', icon: '🤖' },
  { href: '/products', label: 'Products', icon: '📦' },
  { href: '/cart', label: 'Cart', icon: '🛒' },
  { href: '/payments', label: 'Payments', icon: '💳' },
  { href: '/audit', label: 'Audit Trail', icon: '📋' },
  { href: '/analytics', label: 'Analytics', icon: '📈' },
  { href: '/settings', label: 'Settings', icon: '⚙️' },
]

export default function Sidebar() {
  const pathname = usePathname()
  
  return (
    <aside className="w-64 bg-gray-900 text-white flex flex-col">
      <div className="p-4 border-b border-gray-800">
        <h1 className="text-xl font-bold text-primary-400">MerchantFlow AI</h1>
        <p className="text-xs text-gray-400 mt-1">Razorpay Buildathon</p>
      </div>
      
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
              pathname === item.href
                ? 'bg-primary-600 text-white'
                : 'text-gray-300 hover:bg-gray-800 hover:text-white'
            }`}
          >
            <span className="text-lg">{item.icon}</span>
            <span className="text-sm">{item.label}</span>
          </Link>
        ))}
      </nav>
      
      <div className="p-4 border-t border-gray-800 text-xs text-gray-500">
        <p>TEST MODE</p>
        <p>No real money</p>
      </div>
    </aside>
  )
}
