#!/bin/bash
# ============================================
# 服务器启动脚本
# ============================================
# 在服务器上执行: chmod +x start.sh && ./start.sh
# ============================================

set -e

cd /opt/AI-Tutorial

echo "=== 1. 加载环境变量 ==="
if [ -f .env ]; then
    set -a
    source .env
    set +a
    echo "✓ 环境变量已加载"
else
    echo "警告: .env 文件不存在"
fi

echo "=== 2. 停止旧容器 ==="
docker stop aicoding-backend aicoding-frontend 2>/dev/null || true
docker rm aicoding-backend aicoding-frontend 2>/dev/null || true
echo "✓ 完成"

echo "=== 3. 加载镜像 ==="
if [ -f aicoding-frontend-v2.tar ]; then
    echo "加载前端镜像..."
    docker load -i aicoding-frontend-v2.tar
fi
if [ -f aicoding-backend-v3.tar ]; then
    echo "加载后端镜像..."
    docker load -i aicoding-backend-v3.tar
fi
echo "✓ 完成"

echo "=== 4. 启动后端 ==="
docker run -d \
  --name aicoding-backend \
  --restart always \
  -p 8000:8000 \
  -e DATABASE_URL="sqlite+aiosqlite:///./data/data.db" \
  -e SECRET_KEY="${SECRET_KEY}" \
  -e AI_API_KEY="${AI_API_KEY}" \
  -e AI_PROVIDER="${AI_PROVIDER:-siliconflow}" \
  -e AI_MODEL="${AI_MODEL:-Qwen/Qwen2.5-72B-Instruct}" \
  -e AI_BASE_URL="${AI_BASE_URL:-https://api.siliconflow.cn/v1}" \
  -e JUDGE0_BASE_URL="${JUDGE0_BASE_URL:-https://ce.judge0.com}" \
  -e CORS_ORIGINS="http://115.175.38.106:3000" \
  -v /opt/data:/app/data \
  aicoding-backend:v3
echo "✓ 后端已启动"

sleep 3

echo "=== 5. 启动前端 ==="
docker run -d \
  --name aicoding-frontend \
  --restart always \
  -p 3000:3000 \
  aicoding-frontend:v2
echo "✓ 前端已启动"

echo "=== 6. 检查状态 ==="
sleep 2
docker ps

echo ""
echo "============================================"
echo "✓ 启动完成"
echo "访问: http://115.175.38.106:3000"
echo "============================================"
