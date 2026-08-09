import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  distDir: process.env.BUILD_DIST_DIR ?? ".next",
  async rewrites() {
    const apiOrigin = process.env.API_PROXY_TARGET ?? "http://localhost:8000";
    return [
      { source: "/api/:path*", destination: `${apiOrigin}/api/:path*` },
    ];
  },
};

export default nextConfig;
