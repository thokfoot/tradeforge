import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  distDir: process.env.BUILD_DIST_DIR ?? ".next",
  output: process.env.NEXT_EXPORT === "1" ? "export" : "standalone",
  async rewrites() {
    const apiOrigin = process.env.API_PROXY_TARGET ?? "http://localhost:8000";
    return [
      { source: "/api/:path*", destination: `${apiOrigin}/api/:path*` },
    ];
  },
};

export default nextConfig;
