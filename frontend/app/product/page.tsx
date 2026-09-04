'use client'

import { Suspense, useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { sanitizeProductName, formatPrice } from '../utils'

interface Product {
  id: string; name: string; description: string; category: string; subcategory: string;
  brand: string; price: number; previous_price: number | null; cost_price: number | null;
  currency: string; stock: number; sales: number; revenue: number; margin: number;
  sku: string; rating: number; tags: string; image_url: string; is_active: boolean;
}

interface AIQuestion {
  question: string
  answer: string
}

function ProductDetailContent() {
  const searchParams = useSearchParams()
  const productId = searchParams.get('id')
  const [product, setProduct] = useState<Product | null>(null)
  const [loading, setLoading] = useState(true)
  const [quantity, setQuantity] = useState(1)
  const [addingToCart, setAddingToCart] = useState(false)
  const [cartMessage, setCartMessage] = useState('')
  const [aiQuestion, setAiQuestion] = useState('')
  const [aiAnswer, setAiAnswer] = useState('')
  const [aiLoading, setAiLoading] = useState(false)
  const [relatedProducts, setRelatedProducts] = useState<Product[]>([])

  useEffect(() => {
    if (productId) {
      fetchProduct(productId)
      fetchRelated(productId)
    }
  }, [productId])

  const fetchProduct = async (id: string) => {
    setLoading(true)
    try {
      const res = await fetch(`/api/products/${id}`)
      if (res.ok) {
        const data = await res.json()
        setProduct(data)
      }
    } catch (e) {
      console.error('Failed to fetch product')
    } finally {
      setLoading(false)
    }
  }

  const fetchRelated = async (id: string) => {
    try {
      const res = await fetch(`/api/products/?page_size=4&page=1`)
      if (res.ok) {
        const data = await res.json()
        setRelatedProducts((data.products || []).filter((p: Product) => p.id !== id).slice(0, 4))
      }
    } catch (e) {}
  }

  const handleAddToCart = async () => {
    if (!product) return
    setAddingToCart(true)
    setCartMessage('')
    try {
      let sid = localStorage.getItem('session_id')
      if (!sid) { sid = `sess_${Date.now()}`; localStorage.setItem('session_id', sid) }
      const res = await fetch(`/api/carts/session/${sid}/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: product.id, quantity }),
      })
      if (res.ok) {
        setCartMessage(`Added ${quantity} item(s) to cart!`)
        setTimeout(() => setCartMessage(''), 3000)
      } else {
        setCartMessage('Failed to add to cart')
      }
    } catch (e) {
      setCartMessage('Failed to add to cart')
    } finally {
      setAddingToCart(false)
    }
  }

  const handleAskAI = async () => {
    if (!aiQuestion.trim() || !product) return
    setAiLoading(true)
    setAiAnswer('')
    try {
      let sid = localStorage.getItem('session_id') || `sess_${Date.now()}`
      const res = await fetch('/api/agent/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: `About product "${product.name}" (ID: ${product.id}): ${aiQuestion}`,
          session_id: sid,
        }),
      })
      if (res.ok) {
        const data = await res.json()
        setAiAnswer(data.message || 'No response available')
      } else {
        setAiAnswer('AI service is temporarily unavailable. Please try again later.')
      }
    } catch (e) {
      setAiAnswer('Failed to get AI response. Please try again.')
    } finally {
      setAiLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="p-6 lg:p-8 max-w-6xl mx-auto">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-slate-200/70 rounded w-1/4"></div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="h-96 bg-slate-200/70 rounded-xl"></div>
            <div className="space-y-4">
              <div className="h-6 bg-slate-200/70 rounded w-3/4"></div>
              <div className="h-4 bg-slate-200/70 rounded w-1/2"></div>
              <div className="h-10 bg-slate-200/70 rounded w-1/3"></div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!product) {
    return (
      <div className="p-6 lg:p-8 text-center">
        <div className="text-6xl mb-4">📦</div>
        <h2 className="text-xl font-bold text-slate-900 mb-2">Product Not Found</h2>
        <p className="text-slate-500 text-sm mb-4">The product you're looking for doesn't exist or has been removed.</p>
        <a href="/products" className="btn-primary">Browse Products</a>
      </div>
    )
  }

  const discount = product.previous_price && product.previous_price > product.price
    ? Math.round((1 - product.price / product.previous_price) * 100)
    : 0

  return (
    <div className="p-6 lg:p-8 max-w-6xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-xs text-slate-500 mb-6">
        <a href="/" className="hover:text-primary-600 transition-colors">Home</a>
        <span>/</span>
        <a href="/products" className="hover:text-primary-600 transition-colors">Products</a>
        <span>/</span>
        <a href={`/products?category=${product.category}`} className="hover:text-primary-600 transition-colors">{product.category}</a>
        <span>/</span>
        <span className="text-slate-700">{sanitizeProductName(product.name)}</span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
        {/* Product Image */}
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
          <div className="aspect-square flex items-center justify-center bg-gradient-to-br from-slate-100 to-slate-200/70">
            {product.image_url ? (
              <img
                src={product.image_url}
                alt={product.name}
                className="w-full h-full object-cover"
                onError={(e) => {
                  const img = e.target as HTMLImageElement
                  img.onerror = null
                  img.src = 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200"><rect fill="#1e1b4b" width="200" height="200"/><text fill="#6366f1" font-family="Arial" font-size="14" text-anchor="middle" x="100" y="95">📦</text><text fill="#818cf8" font-family="Arial" font-size="11" text-anchor="middle" x="100" y="115">Product</text></svg>')
                }}
              />
            ) : (
              <span className="text-8xl">📦</span>
            )}
          </div>
        </div>

        {/* Product Info */}
        <div className="flex flex-col">
          {/* Brand */}
          {product.brand && (
            <p className="text-xs text-primary-600 font-medium uppercase tracking-wider mb-2">{product.brand}</p>
          )}

          {/* Name */}
          <h1 className="text-2xl lg:text-3xl font-bold text-slate-900 mb-3 leading-tight">
            {sanitizeProductName(product.name)}
          </h1>

          {/* Rating */}
          <div className="flex items-center gap-3 mb-4">
            <div className="flex items-center gap-1">
              {[1, 2, 3, 4, 5].map(star => (
                <span key={star} className={`text-lg ${star <= Math.round(product.rating || 0) ? 'text-amber-500' : 'text-slate-300'}`}>★</span>
              ))}
              <span className="text-sm text-slate-600 ml-2">{product.rating?.toFixed(1) || '0.0'}</span>
            </div>
            <span className="text-xs text-slate-400">({product.sales || 0} sold)</span>
          </div>

          {/* Price */}
          <div className="flex items-baseline gap-3 mb-4">
            <span className="text-3xl font-bold text-slate-900">{formatPrice(product.price)}</span>
            {product.previous_price && product.previous_price > product.price && (
              <>
                <span className="text-lg text-slate-400 line-through">{formatPrice(product.previous_price)}</span>
                <span className="badge-danger text-xs">{discount}% OFF</span>
              </>
            )}
          </div>

          {/* Stock */}
          <div className="mb-6">
            {product.stock > 10 ? (
              <span className="badge-success">In Stock ({product.stock} available)</span>
            ) : product.stock > 0 ? (
              <span className="badge-warning">Low Stock — Only {product.stock} left!</span>
            ) : (
              <span className="badge-danger">Out of Stock</span>
            )}
          </div>

          {/* Description */}
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-slate-900 mb-2">Description</h3>
            <p className="text-sm text-slate-600 leading-relaxed">{product.description}</p>
          </div>

          {/* Specifications */}
          <div className="grid grid-cols-2 gap-3 mb-6">
            <div className="bg-slate-100 rounded-lg p-3">
              <p className="text-[10px] text-slate-500 mb-1">Category</p>
              <p className="text-sm font-medium text-slate-900">{product.category}</p>
            </div>
            {product.subcategory && (
              <div className="bg-slate-100 rounded-lg p-3">
                <p className="text-[10px] text-slate-500 mb-1">Subcategory</p>
                <p className="text-sm font-medium text-slate-900">{product.subcategory}</p>
              </div>
            )}
            {product.sku && (
              <div className="bg-slate-100 rounded-lg p-3">
                <p className="text-[10px] text-slate-500 mb-1">SKU</p>
                <p className="text-sm font-medium text-slate-900 font-mono">{product.sku}</p>
              </div>
            )}
            {product.tags && (
              <div className="bg-slate-100 rounded-lg p-3">
                <p className="text-[10px] text-slate-500 mb-1">Tags</p>
                <p className="text-sm font-medium text-slate-900">{product.tags}</p>
              </div>
            )}
          </div>

          {/* Quantity & Add to Cart */}
          {product.stock > 0 && (
            <div className="flex items-center gap-4 mb-4">
              <div className="flex items-center border border-slate-200 rounded-lg overflow-hidden">
                <button
                  onClick={() => setQuantity(q => Math.max(1, q - 1))}
                  className="px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-900 transition-colors"
                >
                  −
                </button>
                <span className="px-4 py-2.5 text-slate-900 font-medium min-w-[48px] text-center">{quantity}</span>
                <button
                  onClick={() => setQuantity(q => Math.min(product.stock, q + 1))}
                  className="px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-900 transition-colors"
                >
                  +
                </button>
              </div>
              <span className="text-xs text-slate-500">{product.stock} available</span>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3">
            <button
              onClick={handleAddToCart}
              disabled={product.stock <= 0 || addingToCart}
              className="btn-primary flex-1 py-3 text-base"
            >
              {addingToCart ? 'Adding...' : product.stock > 0 ? '🛒 Add to Cart' : 'Out of Stock'}
            </button>
            <a
              href={`/cart`}
              className={`btn-success flex-1 py-3 text-base text-center ${product.stock <= 0 ? 'opacity-50 pointer-events-none' : ''}`}
            >
              {product.stock > 0 ? '⚡ Buy Now' : 'Unavailable'}
            </a>
          </div>

          {/* Cart Message */}
          {cartMessage && (
            <div className={`mt-3 p-3 rounded-lg text-sm ${
              cartMessage.includes('Failed')
                ? 'bg-red-50 text-red-700 border border-red-200'
                : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
            }`}>
              {cartMessage}
            </div>
          )}

          {/* Delivery Info */}
          <div className="mt-6 space-y-2">
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <span className="text-emerald-600">✓</span>
              <span>Free delivery on orders above ₹500</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <span className="text-emerald-600">✓</span>
              <span>7-day return policy</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <span className="text-emerald-600">✓</span>
              <span>Secure payment via Razorpay</span>
            </div>
          </div>
        </div>
      </div>

      {/* AI Product Assistant */}
      <div className="card p-6 mb-8">
        <h3 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
          <span className="text-ai-600">🤖</span> Ask AI about this product
        </h3>
        <p className="text-sm text-slate-500 mb-4">
          Ask questions like &quot;Is this suitable for me?&quot;, &quot;What accessories go with this?&quot;, or &quot;Compare with similar products&quot;
        </p>
        <div className="flex gap-2 mb-4">
          <input
            type="text"
            value={aiQuestion}
            onChange={(e) => setAiQuestion(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAskAI()}
            placeholder={`Ask about ${product.name}...`}
            className="input flex-1"
            disabled={aiLoading}
          />
          <button onClick={handleAskAI} disabled={aiLoading || !aiQuestion.trim()} className="btn-primary px-6">
            {aiLoading ? '...' : 'Ask'}
          </button>
        </div>
        {aiAnswer && (
          <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
            <p className="text-sm text-slate-700 whitespace-pre-wrap leading-relaxed">{aiAnswer}</p>
            <p className="text-[10px] text-slate-400 mt-2 italic">AI-generated response — verify critical information</p>
          </div>
        )}
      </div>

      {/* Related Products */}
      {relatedProducts.length > 0 && (
        <div className="mb-8">
          <h3 className="text-lg font-bold text-slate-900 mb-4">Related Products</h3>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {relatedProducts.map(p => (
              <a
                key={p.id}
                href={`/product?id=${p.id}`}
                className="card-hover p-4 flex flex-col"
              >
                <div className="h-28 bg-slate-100 rounded-lg mb-3 flex items-center justify-center overflow-hidden">
                  {p.image_url ? (
                    <img
                      src={p.image_url}
                      alt={p.name}
                      className="w-full h-full object-cover rounded-lg"
                      loading="lazy"
                      onError={(e) => {
                        const img = e.target as HTMLImageElement
                        img.onerror = null
                        img.src = 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200"><rect fill="#1e1b4b" width="200" height="200"/><text fill="#6366f1" font-family="Arial" font-size="14" text-anchor="middle" x="100" y="95">📦</text><text fill="#818cf8" font-family="Arial" font-size="11" text-anchor="middle" x="100" y="115">Product</text></svg>')
                      }}
                    />
                  ) : (
                    <span className="text-2xl">📦</span>
                  )}
                </div>
                <h4 className="font-medium text-slate-900 text-sm truncate mb-1">{sanitizeProductName(p.name)}</h4>
                <div className="flex items-center gap-1 mb-2">
                  <span className="text-xs text-amber-500">★</span>
                  <span className="text-xs text-slate-600">{p.rating?.toFixed(1) || '-'}</span>
                </div>
                <div className="mt-auto">
                  <span className="text-lg font-bold text-primary-700">{formatPrice(p.price)}</span>
                </div>
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default function ProductDetailPage() {
  return (
    <Suspense fallback={<div className="p-6 lg:p-8 max-w-6xl mx-auto"><div className="animate-pulse space-y-6"><div className="h-8 bg-slate-200/70 rounded w-1/4"></div><div className="h-96 bg-slate-200/70 rounded-xl"></div></div></div>}>
      <ProductDetailContent />
    </Suspense>
  )
}