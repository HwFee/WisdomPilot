# ============================================
# 智码领航前端 - Dockerfile
# ============================================
# 多阶段构建：构建 + 生产镜像
# ============================================

# 构建时参数
ARG NEXT_PUBLIC_API_URL

# 阶段1: 构建
FROM node:20-alpine AS builder

# 接收构建参数
ARG NEXT_PUBLIC_API_URL

# 设置工作目录
WORKDIR /app

# 安装 pnpm
RUN npm install -g pnpm

# 复制依赖文件
COPY package.json pnpm-lock.yaml ./

# 安装依赖
RUN pnpm install --frozen-lockfile

# 复制源代码
COPY . .

# 设置构建时环境变量
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# 构建生产版本
RUN pnpm build

# 阶段2: 生产镜像
FROM node:20-alpine AS runner

WORKDIR /app

# 设置环境变量
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

# 创建非 root 用户
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# 复制构建产物
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# 切换用户
USER nextjs

# 暴露端口
EXPOSE 3000

ENV PORT=3000 \
    HOSTNAME="0.0.0.0"

# 启动命令
CMD ["node", "server.js"]
