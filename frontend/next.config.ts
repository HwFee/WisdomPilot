import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Disable React StrictMode in development to prevent double-rendering
  reactStrictMode: false,

  // 启用 standalone 输出模式，用于 Docker 部署
  output: "standalone",
};

export default nextConfig;
