/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  compress: true,
  poweredByHeader: false,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8000/api/:path*", // Proxy to FastAPI
      },
    ];
  },
  async headers() {
    return [
      {
        // Cloudflare Edge Cache rules for static assets
        source: "/_next/static/:path*",
        headers: [
          {
            key: "Cache-Control",
            value: "public, max-age=31536000, immutable",
          },
          {
            key: "CDN-Cache-Control",
            value: "public, max-age=31536000",
          },
          {
            key: "Cloudflare-CDN-Cache-Control",
            value: "public, max-age=31536000",
          },
        ],
      },
      {
        // Global security & caching headers
        source: "/(.*)",
        headers: [
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "X-Frame-Options",
            value: "DENY",
          },
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin",
          },
          {
            key: "X-Edge-Provider",
            value: "Cloudflare-Pages",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
