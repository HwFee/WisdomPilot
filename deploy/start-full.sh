#!/bin/bash
# ============================================
# 服务器端启动脚本
# ============================================
# 此脚本在服务器上运行，加载镜像并启动容器
# ============================================

set -e

cd /opt/AI-Tutorial

echo "=== 1. 加载环境变量 ==="
if [ -f .env ]; then
    set -a
    source .env
    set +a
else
    echo "警告: .env 文件不存在"
fi

# ===== SECRET_KEY 检查 =====
if [ -z "$SECRET_KEY" ]; then
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    echo "⚠ 未设置 SECRET_KEY，已自动生成: ${SECRET_KEY}"
    echo "⚠ 请将此密钥写入 .env 文件以保持重启后有效"
elif [ ${#SECRET_KEY} -lt 32 ]; then
    echo "❌ SECRET_KEY 长度必须 >= 32 字符（当前: ${#SECRET_KEY}）"
    exit 1
fi

echo "=== 2. 停止并删除旧容器 ==="
docker stop aicoding-backend aicoding-frontend 2>/dev/null || true
docker rm aicoding-backend aicoding-frontend 2>/dev/null || true

echo "=== 3. 加载新镜像 ==="

# 加载前端镜像 v2
if [ -f aicoding-frontend-v2.tar.gz ]; then
    echo "加载前端镜像 v2..."
    gunzip -c aicoding-frontend-v2.tar.gz | docker load
    FRONTEND_IMAGE="aicoding-frontend:v2"
elif docker images | grep -q "aicoding-frontend:v2"; then
    echo "前端镜像 v2 已存在"
    FRONTEND_IMAGE="aicoding-frontend:v2"
else
    echo "错误: 找不到前端镜像 v2"
    exit 1
fi

# 加载后端镜像 v3
if [ -f aicoding-backend-v3.tar.gz ]; then
    echo "加载后端镜像 v3..."
    gunzip -c aicoding-backend-v3.tar.gz | docker load
    BACKEND_IMAGE="aicoding-backend:v3"
elif docker images | grep -q "aicoding-backend:v3"; then
    echo "后端镜像 v3 已存在"
    BACKEND_IMAGE="aicoding-backend:v3"
else
    echo "错误: 找不到后端镜像 v3"
    exit 1
fi

echo "=== 4. 启动后端服务 ==="
docker run -d \
  --name aicoding-backend \
  --restart always \
  -p 8000:8000 \
  -e DEBUG=false \
  -e SECRET_KEY="${SECRET_KEY}" \
  -e AI_PROVIDER="${AI_PROVIDER:-siliconflow}" \
  -e AI_API_KEY="${AI_API_KEY}" \
  -e AI_MODEL="${AI_MODEL:-Qwen/Qwen2.5-72B-Instruct}" \
  -e AI_BASE_URL="${AI_BASE_URL:-https://api.siliconflow.cn/v1}" \
  -e MINIMAX_API_KEY="${MINIMAX_API_KEY:-}" \
  -e MINIMAX_MODEL="${MINIMAX_MODEL:-MiniMax-M2.7}" \
  -e EMBEDDING_PROVIDER="${EMBEDDING_PROVIDER:-siliconflow}" \
  -e EMBEDDING_API_KEY="${EMBEDDING_API_KEY:-}" \
  -e EMBEDDING_BASE_URL="${EMBEDDING_BASE_URL:-https://api.siliconflow.cn/v1}" \
  -e EMBEDDING_MODEL="${EMBEDDING_MODEL:-BAAI/bge-large-zh-v1.5}" \
  -e JUDGE0_BASE_URL="${JUDGE0_BASE_URL:-https://ce.judge0.com}" \
  -e ENABLE_TEST_SANDBOX=false \
  -e CORS_ORIGINS="${CORS_ORIGINS:-http://115.175.38.106:3000}" \
  -e DATABASE_URL="sqlite+aiosqlite:///./data/data.db" \
  -v /opt/data:/app/data \
  ${BACKEND_IMAGE}

echo "等待后端启动..."
sleep 5

echo "=== 5. 启动前端服务 ==="
docker run -d \
  --name aicoding-frontend \
  --restart always \
  -p 3000:3000 \
  ${FRONTEND_IMAGE}

echo "=== 6. 检查服务状态 ==="
sleep 3
echo ""
echo "--- 容器状态 ---"
docker ps

echo ""
echo "--- 后端日志 (最后10行) ---"
docker logs aicoding-backend --tail 10

echo ""
echo "============================================"
echo "✓ 启动完成！"
echo "访问: http://115.175.38.106:3000"
echo "============================================"
