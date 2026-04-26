#!/bin/bash
# ============================================
# 智码领航 - 完整部署脚本
# ============================================
# 在 Git Bash 中执行: bash deploy.sh
# ============================================

set -e

# 配置
SERVER_IP="115.175.38.106"
SERVER_USER="root"
SERVER_DIR="/opt/AI-Tutorial"
API_URL="http://${SERVER_IP}:8000"

echo "============================================"
echo "智码领航 - 完整部署"
echo "服务器: ${SERVER_IP}"
echo "API地址: ${API_URL}"
echo "============================================"

# 1. 构建前端（关键：传入API地址，构建时注入到JS中）
echo ""
echo "[1/6] 构建前端镜像..."
cd frontend
docker build --build-arg NEXT_PUBLIC_API_URL="${API_URL}" -t aicoding-frontend:v2 .
cd ..
echo "✓ 完成"

# 2. 构建后端
echo ""
echo "[2/6] 构建后端镜像..."
cd backend
docker build -t aicoding-backend:v3 .
cd ..
echo "✓ 完成"

# 3. 导出镜像（压缩以加快传输）
echo ""
echo "[3/6] 导出并压缩镜像..."
docker save aicoding-frontend:v2 | gzip > aicoding-frontend-v2.tar.gz
docker save aicoding-backend:v3 | gzip > aicoding-backend-v3.tar.gz
echo "✓ 完成"

# 4. 上传到服务器
echo ""
echo "[4/6] 上传镜像到服务器..."
scp aicoding-frontend-v2.tar.gz aicoding-backend-v3.tar.gz ${SERVER_USER}@${SERVER_IP}:${SERVER_DIR}/
echo "✓ 完成"

# 5. 服务器启动
echo ""
echo "[5/6] 服务器启动服务..."
ssh ${SERVER_USER}@${SERVER_IP} << ENDSSH
cd ${SERVER_DIR}

# 加载环境变量
[ -f .env ] && { set -a; source .env; set +a; }

# ===== SECRET_KEY 检查 =====
if [ -z "\$SECRET_KEY" ]; then
    SECRET_KEY=\$(python3 -c "import secrets; print(secrets.token_hex(32))")
    echo "⚠ 未设置 SECRET_KEY，已自动生成: \${SECRET_KEY}"
    echo "⚠ 请将此密钥写入 .env 文件以保持重启后有效"
elif [ \${#SECRET_KEY} -lt 32 ]; then
    echo "❌ SECRET_KEY 长度必须 >= 32 字符（当前: \${#SECRET_KEY}）"
    exit 1
fi

# 停止旧容器
docker stop aicoding-backend aicoding-frontend 2>/dev/null || true
docker rm aicoding-backend aicoding-frontend 2>/dev/null || true

# 加载新镜像
gunzip -c aicoding-frontend-v2.tar.gz | docker load
gunzip -c aicoding-backend-v3.tar.gz | docker load

# 启动后端
docker run -d --name aicoding-backend --restart always -p 8000:8000 \
  -e SECRET_KEY="\${SECRET_KEY}" \
  -e AI_API_KEY="\${AI_API_KEY}" \
  -e AI_PROVIDER="\${AI_PROVIDER:-siliconflow}" \
  -e AI_MODEL="\${AI_MODEL:-Qwen/Qwen2.5-72B-Instruct}" \
  -e AI_BASE_URL="\${AI_BASE_URL:-https://api.siliconflow.cn/v1}" \
  -e JUDGE0_BASE_URL="\${JUDGE0_BASE_URL:-https://ce.judge0.com}" \
  -e ENABLE_TEST_SANDBOX=false \
  -e CORS_ORIGINS="http://${SERVER_IP}:3000" \
  -e DATABASE_URL="sqlite+aiosqlite:///./data/data.db" \
  -v /opt/data:/app/data \
  aicoding-backend:v3

sleep 5

# 启动前端
docker run -d --name aicoding-frontend --restart always -p 3000:3000 aicoding-frontend:v2

sleep 3

# 6. 健康检查
echo ""
echo "[6/6] 健康检查..."
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 后端健康检查
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ 后端正常"
else
    echo "✗ 后端异常，日志："
    docker logs aicoding-backend --tail 20
fi

# 前端健康检查
if curl -sf http://localhost:3000 > /dev/null 2>&1; then
    echo "✓ 前端正常"
else
    echo "✗ 前端异常，日志："
    docker logs aicoding-frontend --tail 20
fi
ENDSSH

echo ""
echo "============================================"
echo "✓ 部署完成: http://${SERVER_IP}:3000"
echo "============================================"

# 清理本地 tar.gz 文件（可选）
# rm -f aicoding-frontend-v2.tar.gz aicoding-backend-v3.tar.gz
