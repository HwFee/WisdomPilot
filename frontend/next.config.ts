import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Disable React StrictMode in development to prevent double-rendering
  reactStrictMode: false,

  // 启用 standalone 输出模式，用于 Docker 部署
  output: "standalone",

  // Keep Next from walking up to parent tool worktrees and picking their lockfiles.
  outputFileTracingRoot: process.cwd(),
};

export default nextConfig;
