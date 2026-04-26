#!/bin/bash
# ============================================
# 一键部署脚本 - 本地构建 + 上传服务器
# ============================================
# 使用方法: ./deploy-full.sh
# ============================================

set -e

# ============================================
# 配置区 - 根据你的服务器修改
# ============================================
SERVER_IP="115.175.38.106"
SERVER_USER="root"
SERVER_DIR="/opt/AI-Tutorial"
LOCAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# 前端 API 地址（重要！）
FRONTEND_API_URL="http://${SERVER_IP}:8000"

echo "============================================"
echo "智码领航 - 完整部署脚本"
echo "============================================"
echo "服务器: ${SERVER_USER}@${SERVER_IP}"
echo "前端API: ${FRONTEND_API_URL}"
echo "本地目录: ${LOCAL_DIR}"
echo "============================================"

# ============================================
# 第一步：构建前端镜像（带正确的API地址）
# ============================================
echo ""
echo "=== [1/5] 构建前端镜像 ==="
echo "API URL: ${FRONTEND_API_URL}"

cd "${LOCAL_DIR}/frontend"

docker build \
  --build-arg NEXT_PUBLIC_API_URL="${FRONTEND_API_URL}" \
  -t aicoding-frontend:v2 \
  .

echo "✓ 前端镜像构建完成: aicoding-frontend:v2"

# ============================================
# 第二步：构建后端镜像
# ============================================
echo ""
echo "=== [2/5] 构建后端镜像 ==="

cd "${LOCAL_DIR}/backend"

docker build \
  -t aicoding-backend:v3 \
  .

echo "✓ 后端镜像构建完成: aicoding-backend:v3"

# ============================================
# 第三步：导出镜像文件
# ============================================
echo ""
echo "=== [3/5] 导出镜像文件 ==="

cd "${LOCAL_DIR}"

echo "导出前端镜像..."
docker save aicoding-frontend:v2 | gzip > aicoding-frontend-v2.tar.gz
echo "✓ aicoding-frontend-v2.tar.gz"

echo "导出后端镜像..."
docker save aicoding-backend:v3 | gzip > aicoding-backend-v3.tar.gz
echo "✓ aicoding-backend-v3.tar.gz"

# ============================================
# 第四步：上传到服务器
# ============================================
echo ""
echo "=== [4/5] 上传到服务器 ==="

echo "上传前端镜像..."
scp aicoding-frontend-v2.tar.gz ${SERVER_USER}@${SERVER_IP}:${SERVER_DIR}/
echo "✓ 前端镜像上传完成"

echo "上传后端镜像..."
scp aicoding-backend-v3.tar.gz ${SERVER_USER}@${SERVER_IP}:${SERVER_DIR}/
echo "✓ 后端镜像上传完成"

echo "上传启动脚本..."
scp deploy/start-full.sh ${SERVER_USER}@${SERVER_IP}:${SERVER_DIR}/start.sh
chmod +x ${SERVER_DIR}/start.sh 2>/dev/null || true
echo "✓ 启动脚本上传完成"

# ============================================
# 第五步：在服务器上启动
# ============================================
echo ""
echo "=== [5/5] 在服务器上启动服务 ==="

ssh ${SERVER_USER}@${SERVER_IP} "cd ${SERVER_DIR} && chmod +x start.sh && ./start.sh"

echo ""
echo "============================================"
echo "✓ 部署完成！"
echo "访问: http://${SERVER_IP}:3000"
echo "============================================"
