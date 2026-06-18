import type { NextConfig } from "next";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  // Disable React StrictMode in development to prevent double-rendering
  reactStrictMode: false,

  // 启用 standalone 输出模式，用于 Docker 部署
  output: "standalone",

  // Keep Next from walking up to parent tool worktrees and picking their lockfiles.
  outputFileTracingRoot: process.cwd(),

  // Proxy API requests to the backend during development to avoid CORS issues
  // caused by browsers/network environments stripping CORS response headers.
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${API_BASE_URL}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
