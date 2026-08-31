'use client'

import { useEffect, useState, useCallback } from 'react'
import { sanitizeProductName, formatPrice } from '../utils'

interface Product {
  id: string; name: string; description: string; category: string; subcategory: string;
  brand: string; price: number; previous_price: number | null; cost_price: number | null;
  currency: string; stock: number; sales: number; revenue: number; margin: number;
  sku: string; rating: number; tags: string; image_url: string; is_active: boolean;
}

interface PricingRecommendation {
  product_id: string; product_name: string; current_price: number;
  recommended_price: number; expected_revenue_impact: number;
  expected_margin_impact: number; confidence: number; explanation: string; direction: string;
}

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [sortBy, setSortBy] = useState('name')
  const [sortOrder, setSortOrder] = useState('asc')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [total, setTotal] = useState(0)
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
  const [categories, setCategories] = useState<{name: string; count: number}[]>([])
  const [showPricing, setShowPricing] = useState<PricingRecommendation | null>(null)
  const [editingProduct, setEditingProduct] = useState<Product | null>(null)
  const [editPrice, setEditPrice] = useState('')
  const [editStock, setEditStock] = useState('')
  const [addingToCart, setAddingToCart] = useState<string | null>(null)

  const fetchProducts = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ page: String(page), page_size: '20', sort_by: sortBy, sort_order: sortOrder })
      if (search) params.set('q', search)
      if (category) params.set('category', category)
      const res = await fetch(`/api/products/?${params}`)
      const data = await res.json()
      setProducts(data.products || [])
      setTotalPages(data.total_pages || 1)
      setTotal(data.total || 0)
    } catch (e) { console.error('Failed to fetch products') }
    finally { setLoading(false) }
  }, [page, search, category, sortBy, sortOrder])

  useEffect(() => { fetchProducts() }, [fetchProducts])

  useEffect(() => {
    fetch('/api/products/categories')
      .then(r => r.json()).then(setCategories).catch(() => {})
  }, [])

  const handleAddToCart = async (productId: string) => {
    setAddingToCart(productId)
    try {
      const sid = localStorage.getItem('session_id') || `sess_${Date.now()}`
      localStorage.setItem('session_id', sid)
      await fetch(`/api/carts/session/${sid}/add`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: productId, quantity: 1 }),
      })
    } catch (e) { console.error('Add to cart failed') }
    finally { setAddingToCart(null) }
  }

  const handleGetPricing = async (productId: string) => {
    try {
      const res = await fetch(`/api/pricing/recommend/${productId}`)
      const data = await res.json()
      setShowPricing(data)
    } catch (e) { console.error('Pricing failed') }
  }

  const handleApplyPrice = async (productId: string, newPrice: number) => {
    try {
      await fetch(`/api/pricing/apply`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: productId, new_price: newPrice }),
      })
      setShowPricing(null)
      setEditingProduct(null)
      fetchProducts()
    } catch (e) { console.error('Apply price failed') }
  }

  const handleSaveEdit = async () => {
    if (!editingProduct) return
    const body: any = {}
    if (editPrice) body.price = parseFloat(editPrice)
    if (editStock) body.stock = parseInt(editStock)
    try {
      await fetch(`/api/products/${editingProduct.id}`, {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      setEditingProduct(null)
      fetchProducts()
    } catch (e) { console.error('Update failed') }
  }

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Product Catalog</h1>
          <p className="text-dark-400 text-sm mt-1">{total.toLocaleString()} products · Server-side pagination</p>
        </div>
      </div>

      {/* Search & Filters */}
      <div className="card p-4 mb-6">
        <div className="flex flex-col lg:flex-row gap-3">
          <div className="flex-1">
            <input
              type="text" value={search} onChange={e => { setSearch(e.target.value); setPage(1) }}
              placeholder="Search products by name, brand, category..."
              className="input"
            />
          </div>
          <select value={category} onChange={e => { setCategory(e.target.value); setPage(1) }} className="input w-full lg:w-48">
            <option value="">All Categories</option>
            {categories.map(c => (
              <option key={c.name} value={c.name}>{c.name} ({c.count})</option>
            ))}
          </select>
          <select value={`${sortBy}_${sortOrder}`} onChange={e => {
            const [sb, so] = e.target.value.split('_'); setSortBy(sb); setSortOrder(so)
          }} className="input w-full lg:w-48">
            <option value="name_asc">Name A-Z</option>
            <option value="name_desc">Name Z-A</option>
            <option value="price_asc">Price Low-High</option>
            <option value="price_desc">Price High-Low</option>
            <option value="stock_desc">Stock High-Low</option>
            <option value="rating_desc">Rating High-Low</option>
            <option value="sales_desc">Sales Best</option>
          </select>
        </div>
      </div>

      {/* Product Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="card p-4 animate-pulse">
              <div className="h-32 bg-dark-700 rounded mb-3"></div>
              <div className="h-4 bg-dark-700 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-dark-700 rounded w-1/2 mb-4"></div>
              <div className="h-6 bg-dark-700 rounded w-1/3"></div>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {products.map(product => (
            <div key={product.id} className="card-hover p-4 flex flex-col cursor-pointer" onClick={() => setSelectedProduct(product)}>
              {/* Image placeholder */}
              <div className="h-28 bg-dark-700 rounded-lg mb-3 flex items-center justify-center overflow-hidden">
                {product.image_url ? (
                  <img src={product.image_url} alt={product.name} className="w-full h-full object-cover rounded-lg" onError={e => (e.target as HTMLImageElement).style.display='none'} />
                ) : (
                  <span className="text-2xl">📦</span>
                )}
              </div>

              <div className="flex items-start justify-between mb-1">
                <h3 className="font-semibold text-white text-sm leading-tight flex-1 truncate">{sanitizeProductName(product.name)}</h3>
                {product.stock > 0 ? (
                  <span className="badge-success text-[10px] ml-2 flex-shrink-0">{product.stock}</span>
                ) : (
                  <span className="badge-danger text-[10px] ml-2 flex-shrink-0">Out</span>
                )}
              </div>

              <p className="text-xs text-dark-400 mb-2 line-clamp-2">{product.description}</p>

              <div className="flex items-center gap-1 mb-2">
                <span className="text-xs text-amber-400">★</span>
                <span className="text-xs text-dark-300">{product.rating?.toFixed(1) || '-'}</span>
                <span className="text-xs text-dark-500 ml-1">· {product.brand}</span>
              </div>

              <div className="mt-auto">
                <div className="flex items-baseline gap-2">
                  <span className="text-lg font-bold text-primary-400">₹{product.price.toLocaleString()}</span>
                  {product.previous_price && product.previous_price > product.price && (
                    <span className="text-xs text-dark-500 line-through">₹{product.previous_price.toLocaleString()}</span>
                  )}
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-[10px] text-dark-500">{product.category}</span>
                  {product.margin > 0 && (
                    <span className="text-[10px] text-emerald-400">{product.margin.toFixed(0)}% margin</span>
                  )}
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); handleAddToCart(product.id) }}
                  disabled={product.stock <= 0 || addingToCart === product.id}
                  className="btn-primary w-full mt-3 text-xs py-1.5"
                >
                  {addingToCart === product.id ? 'Adding...' : product.stock > 0 ? '+ Add to Cart' : 'Out of Stock'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-6">
          <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
            className="btn-secondary text-xs px-3 py-1.5">← Prev</button>
          <span className="text-sm text-dark-300">Page {page} of {totalPages} ({total.toLocaleString()} products)</span>
          <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}
            className="btn-secondary text-xs px-3 py-1.5">Next →</button>
        </div>
      )}

      {/* Product Detail Modal */}
      {selectedProduct && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4" onClick={() => setSelectedProduct(null)}>
          <div className="bg-dark-800 border border-dark-600 rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h2 className="text-xl font-bold text-white">{sanitizeProductName(selectedProduct.name)}</h2>
                  <p className="text-sm text-dark-400">{selectedProduct.brand} · {selectedProduct.sku}</p>
                </div>
                <button onClick={() => setSelectedProduct(null)} className="text-dark-400 hover:text-white text-xl">✕</button>
              </div>

              <div className="grid grid-cols-2 lg:grid-cols-3 gap-3 mb-6">
                <InfoBox label="Price" value={`₹${selectedProduct.price.toLocaleString()}`} />
                <InfoBox label="Cost Price" value={`₹${(selectedProduct.cost_price || 0).toLocaleString()}`} />
                <InfoBox label="Margin" value={`${selectedProduct.margin?.toFixed(1)}%`} highlight={selectedProduct.margin > 20} />
                <InfoBox label="Stock" value={String(selectedProduct.stock)} warn={selectedProduct.stock <= 10} />
                <InfoBox label="Sales" value={String(selectedProduct.sales || 0)} />
                <InfoBox label="Revenue" value={`₹${(selectedProduct.revenue || 0).toLocaleString()}`} />
                <InfoBox label="Rating" value={`${selectedProduct.rating?.toFixed(1)} ★`} />
                <InfoBox label="Category" value={selectedProduct.category} />
                <InfoBox label="Subcategory" value={selectedProduct.subcategory || '-'} />
              </div>

              <p className="text-sm text-dark-300 mb-4">{selectedProduct.description}</p>

              <div className="flex gap-2">
                <button onClick={() => handleAddToCart(selectedProduct.id)} disabled={selectedProduct.stock <= 0}
                  className="btn-primary flex-1">+ Add to Cart</button>
                <button onClick={() => handleGetPricing(selectedProduct.id)} className="btn-secondary flex-1">🤖 AI Price</button>
                <button onClick={() => {
                  setEditingProduct(selectedProduct)
                  setEditPrice(String(selectedProduct.price))
                  setEditStock(String(selectedProduct.stock))
                }} className="btn-secondary flex-1">✏️ Edit</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Pricing Recommendation Modal */}
      {showPricing && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4" onClick={() => setShowPricing(null)}>
          <div className="bg-dark-800 border border-dark-600 rounded-xl max-w-lg w-full p-6" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-white mb-4">🤖 AI Pricing Recommendation</h3>
            <div className="space-y-3 mb-4">
              <div className="flex justify-between text-sm">
                <span className="text-dark-400">Current Price</span>
                <span className="text-white font-semibold">₹{showPricing.current_price.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-dark-400">Recommended Price</span>
                <span className={`font-semibold ${showPricing.direction === 'increase' ? 'text-emerald-400' : showPricing.direction === 'decrease' ? 'text-amber-400' : 'text-dark-200'}`}>
                  ₹{showPricing.recommended_price.toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-dark-400">Revenue Impact</span>
                <span className={`font-semibold ${showPricing.expected_revenue_impact > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {showPricing.expected_revenue_impact > 0 ? '+' : ''}₹{showPricing.expected_revenue_impact.toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-dark-400">Confidence</span>
                <span className="text-white font-semibold">{(showPricing.confidence * 100).toFixed(0)}%</span>
              </div>
            </div>
            <div className="bg-dark-700 rounded-lg p-3 mb-4">
              <p className="text-xs text-dark-300">{showPricing.explanation}</p>
              <p className="text-[10px] text-dark-500 mt-1 italic">* AI estimates — not guaranteed outcomes</p>
            </div>
            <div className="flex gap-2">
              <button onClick={() => handleApplyPrice(showPricing.product_id, showPricing.recommended_price)}
                className="btn-success flex-1">Apply Price</button>
              <button onClick={() => setShowPricing(null)} className="btn-secondary flex-1">Cancel</button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Product Modal */}
      {editingProduct && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4" onClick={() => setEditingProduct(null)}>
          <div className="bg-dark-800 border border-dark-600 rounded-xl max-w-md w-full p-6" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-white mb-4">Edit Product</h3>
            <div className="space-y-3">
              <div>
                <label className="text-xs text-dark-400 mb-1 block">Price (₹)</label>
                <input type="number" value={editPrice} onChange={e => setEditPrice(e.target.value)} className="input" />
              </div>
              <div>
                <label className="text-xs text-dark-400 mb-1 block">Stock</label>
                <input type="number" value={editStock} onChange={e => setEditStock(e.target.value)} className="input" />
              </div>
            </div>
            <div className="flex gap-2 mt-4">
              <button onClick={handleSaveEdit} className="btn-primary flex-1">Save Changes</button>
              <button onClick={() => setEditingProduct(null)} className="btn-secondary flex-1">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function InfoBox({ label, value, highlight, warn }: {
  label: string; value: string; highlight?: boolean; warn?: boolean
}) {
  return (
    <div className="bg-dark-700/50 rounded-lg p-2.5">
      <p className="text-[10px] text-dark-400 mb-0.5">{label}</p>
      <p className={`text-sm font-semibold ${highlight ? 'text-emerald-400' : warn ? 'text-amber-400' : 'text-white'}`}>{value}</p>
    </div>
  )
}
