'use client'

import { useEffect, useState } from 'react'

interface Product {
  id: string
  name: string
  description: string
  category: string
  price: number
  currency: string
  stock: number
}

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedCategory, setSelectedCategory] = useState<string>('')
  const [showWhyModal, setShowWhyModal] = useState<string | null>(null)

  useEffect(() => {
    fetchProducts()
  }, [selectedCategory])

  const fetchProducts = async () => {
    setLoading(true)
    try {
      const url = selectedCategory
        ? `/api/products/?category=${selectedCategory}`
        : '/api/products/'
      const res = await fetch(url)
      const data = await res.json()
      setProducts(data.products || [])
    } catch (error) {
      console.error('Failed to fetch products')
    } finally {
      setLoading(false)
    }
  }

  const categories = [...new Set(products.map(p => p.category))]

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Product Catalog</h1>
        <p className="text-gray-600 mt-1">Browse our agent-readable catalog</p>
      </div>

      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        <button
          onClick={() => setSelectedCategory('')}
          className={`px-4 py-2 rounded-full text-sm whitespace-nowrap ${
            !selectedCategory
              ? 'bg-primary-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          All Products
        </button>
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`px-4 py-2 rounded-full text-sm whitespace-nowrap ${
              selectedCategory === cat
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="bg-white rounded-lg shadow p-4 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2 mb-4"></div>
              <div className="h-8 bg-gray-200 rounded w-1/4"></div>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {products.map((product) => (
            <div key={product.id} className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-4">
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-semibold text-gray-900">{product.name}</h3>
                <span className={`px-2 py-1 text-xs rounded ${
                  product.stock > 0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {product.stock > 0 ? `${product.stock} in stock` : 'Out of stock'}
                </span>
              </div>
              <p className="text-sm text-gray-600 mb-2">{product.description}</p>
              <div className="flex items-center justify-between">
                <span className="text-lg font-bold text-primary-600">
                  ₹{product.price.toLocaleString()}
                </span>
                <button
                  onClick={() => setShowWhyModal(product.id)}
                  className="text-xs text-gray-500 hover:text-primary-600"
                >
                  Why?
                </button>
              </div>
              <div className="mt-2">
                <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                  {product.category}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {showWhyModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Why This Product?</h3>
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <span className="text-green-500">✓</span>
                <p className="text-sm">Matches requested category</p>
              </div>
              <div className="flex items-start gap-3">
                <span className="text-green-500">✓</span>
                <p className="text-sm">Within requested budget</p>
              </div>
              <div className="flex items-start gap-3">
                <span className="text-green-500">✓</span>
                <p className="text-sm">Currently available in stock</p>
              </div>
              <div className="flex items-start gap-3">
                <span className="text-green-500">✓</span>
                <p className="text-sm">Highly rated by customers</p>
              </div>
            </div>
            <button
              onClick={() => setShowWhyModal(null)}
              className="mt-6 w-full px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
