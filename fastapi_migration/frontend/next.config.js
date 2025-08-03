/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Use Turbopack (now stable) for development
  turbopack: {
    // Add Turbopack-specific options here if needed
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_ENABLE_PASSWORD_CHANGE: process.env.NEXT_PUBLIC_ENABLE_PASSWORD_CHANGE || 'true',
  },
  allowedDevOrigins: ['127.0.0.1', 'localhost'],  // Add this to fix the cross-origin warning
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/:path*`,
      },
    ]
  },
}

module.exports = nextConfig