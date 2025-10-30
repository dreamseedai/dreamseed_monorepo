/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    typedRoutes: true,
    serverActions: {
      allowedOrigins: ["localhost:3030", "127.0.0.1:3030", "192.168.68.116:3030"],
    },
  },
  async rewrites() {
    return [
      {
        source: '/api/seedtest/:path*',
        destination: 'http://127.0.0.1:8012/api/seedtest/:path*',
      },
      // Proxy editor images to the API/static server to avoid 404s like /images/editor/18891.png
      {
        source: '/images/editor/:path*',
        destination: 'http://127.0.0.1:8012/images/editor/:path*',
      },
    ];
  },
};
export default nextConfig;
