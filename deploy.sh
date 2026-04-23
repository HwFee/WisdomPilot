#!/bin/bash
# ============================================
# 智码领航 - 简化部署脚本
# ============================================
# 适用于华为云服务器（无域名版本）
# 直接重建容器，有短暂停机（约10秒）
# ============================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 项目目录
PROJECT_DIR="/opt/AI-Tutorial"
cd $PROJECT_DIR

log_info "=== 1. 拉取最新代码 ==="
git pull origin main

log_info "=== 2. 读取环境变量 ==="
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    log_info "环境变量已加载"
else
    log_warn "未找到 .env 文件"
fi

log_info "=== 3. 重建并启动后端 ==="
docker-compose stop backend || true
docker-compose rm -f backend || true
docker-compose build --no-cache backend
docker-compose up -d backend

log_info "=== 4. 等待后端启动 ==="
sleep 5

MAX_RETRIES=12
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -sf http://127.0.0.1:8000/health > /dev/null 2>&1; then
        log_info "后端启动成功！"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    log_warn "等待后端启动... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 3
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    log_error "后端启动失败！"
    exit 1
fi

log_info "=== 5. 重建并启动前端 ==="
docker-compose stop frontend || true
docker-compose rm -f frontend || true
docker-compose build --no-cache frontend
docker-compose up -d frontend

log_info "=== 部署完成！==="
log_info "访问地址: http://115.175.38.106:3000"
