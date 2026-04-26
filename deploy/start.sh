#!/bin/bash
set -e

cd /opt/AI-Tutorial

echo "=== 1. 加载环境变量 ==="
set -a
source .env
set +a

echo "=== 2. 清理旧容器 ==="
docker stop aicoding-backend aicoding-frontend 2>/dev/null || true
docker rm aicoding-backend aicoding-frontend 2>/dev/null || true

echo "=== 3. 加载镜像 ==="
if ! docker images | grep -q "aicoding-backend:v3"; then
    echo "加载后端镜像 v3..."
    gunzip -c aicoding-backend-v3.tar.gz | docker load
fi
if ! docker images | grep -q "aicoding-frontend:v1"; then
    echo "加载前端镜像..."
    gunzip -c aicoding-frontend-v1.tar.gz | docker load
fi

echo "=== 4. 启动后端 v3 ==="
docker run -d \
  --name aicoding-backend \
  --restart always \
  -p 8000:8000 \
  -e DEBUG=false \
  -e SECRET_KEY="$SECRET_KEY" \
  -e AI_PROVIDER="${AI_PROVIDER:-siliconflow}" \
  -e AI_API_KEY="$AI_API_KEY" \
  -e AI_MODEL="${AI_MODEL:-Qwen/Qwen2.5-72B-Instruct}" \
  -e AI_BASE_URL="${AI_BASE_URL:-https://api.siliconflow.cn/v1}" \
  -e MINIMAX_API_KEY="$MINIMAX_API_KEY" \
  -e MINIMAX_MODEL="${MINIMAX_MODEL:-MiniMax-M2.7}" \
  -e EMBEDDING_PROVIDER="${EMBEDDING_PROVIDER:-siliconflow}" \
  -e EMBEDDING_API_KEY="$EMBEDDING_API_KEY" \
  -e EMBEDDING_BASE_URL="${EMBEDDING_BASE_URL:-https://api.siliconflow.cn/v1}" \
  -e EMBEDDING_MODEL="${EMBEDDING_MODEL:-BAAI/bge-large-zh-v1.5}" \
  -e JUDGE0_BASE_URL="${JUDGE0_BASE_URL:-https://ce.judge0.com}" \
  -e ENABLE_TEST_SANDBOX=false \
  -e CORS_ORIGINS="${CORS_ORIGINS:-http://115.175.38.106:3000}" \
  -e DATABASE_URL="sqlite+aiosqlite:///./data/data.db" \
  -v /opt/data:/app/data \
  aicoding-backend:v3

echo "=== 5. 启动前端 ==="
docker run -d \
  --name aicoding-frontend \
  --restart always \
  -p 3000:3000 \
  aicoding-frontend:v1

echo "=== 6. 检查状态 ==="
sleep 3
docker ps

echo "=== 7. 后端日志 ==="
docker logs aicoding-backend --tail 15

echo "=== 启动完成 ==="
echo "访问: http://115.175.38.106:3000"
