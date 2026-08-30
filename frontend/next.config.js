/** @type {import('next').NextConfig} */

const nextConfig = {
  // Static export - produces HTML/JS/CSS in /out directory
  // No Next.js server needed; FastAPI serves these files
  output: 'export',

  // Disable image optimization for static export
  images: {
    unoptimized: true,
  },

  // Security headers
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
        ],
      },
    ]
  },
}

module.exports = nextConfig
