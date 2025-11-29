/** @type {import('next').NextConfig} */
const nextConfig = {
  // Production optimizations
  reactStrictMode: true,
  poweredByHeader: false,
  
  // Standalone output for easier deployment
  output: 'standalone',
  
  // Image optimization
  images: {
    domains: ['dreamseedai.com'],
    unoptimized: false,
  },
  
  // Compression
  compress: true,
  
  // Asset prefix for CDN (optional - uncomment if using CDN)
  // assetPrefix: process.env.NEXT_PUBLIC_CDN_URL,
  
  // Disable x-powered-by header
  generateEtags: true,
  
  // Production source maps (disable for smaller build size)
  productionBrowserSourceMaps: false,
  
  // Custom webpack config if needed
  webpack: (config, { isServer }) => {
    // Add custom webpack configurations here if needed
    return config;
  },
  
  // Environment variables available to the browser
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
  },
  
  // Redirects (removed automatic redirect to /questions)
  async redirects() {
    return [];
  },
};
module.exports = nextConfig;
