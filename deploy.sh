#!/bin/bash
# ============================================
# 智码领航 - 一键部署脚本
# ============================================
# 适用于华为云服务器
# 实现蓝绿部署，零停机更新
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

log_info "=== 1. 拉取最新代码（Gitee） ==="
git pull origin main

log_info "=== 2. 判断当前活跃实例 ==="
# 检查哪个实例正在运行
if curl -sf http://127.0.0.1:8001/health > /dev/null 2>&1; then
    ACTIVE="green"
    STANDBY="blue"
    ACTIVE_PORT=8001
    STANDBY_PORT=8002
else
    ACTIVE="blue"
    STANDBY="green"
    ACTIVE_PORT=8002
    STANDBY_PORT=8001
fi
log_info "当前活跃实例: $ACTIVE (端口 $ACTIVE_PORT)，备用实例: $STANDBY (端口 $STANDBY_PORT)"

log_info "=== 3. 构建并重启备用实例 ==="
docker-compose stop backend-$STANDBY || true
docker-compose rm -f backend-$STANDBY || true
docker-compose build backend-$STANDBY
docker-compose up -d backend-$STANDBY

log_info "=== 4. 等待备用实例启动 ==="
sleep 10

# 健康检查
MAX_RETRIES=12
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -sf http://127.0.0.1:$STANDBY_PORT/health > /dev/null 2>&1; then
        log_info "备用实例启动成功！"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    log_warn "等待备用实例启动... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 5
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    log_error "备用实例启动失败，回滚！"
    docker-compose up -d backend-$ACTIVE
    exit 1
fi

log_info "=== 5. 切换 Nginx 流量到备用实例 ==="
# 更新 Nginx upstream 配置
if [ "$STANDBY" == "green" ]; then
    # Green 为主，Blue 为备
    sed -i 's/server 127.0.0.1:800[12]/server 127.0.0.1:8001;/' /etc/nginx/conf.d/app.conf
    sed -i 's/server 127.0.0.1:800[12] backup/server 127.0.0.1:8002 backup;/' /etc/nginx/conf.d/app.conf
else
    # Blue 为主，Green 为备
    sed -i 's/server 127.0.0.1:800[12]/server 127.0.0.1:8002;/' /etc/nginx/conf.d/app.conf
    sed -i 's/server 127.0.0.1:800[12] backup/server 127.0.0.1:8001 backup;/' /etc/nginx/conf.d/app.conf
fi

nginx -t && nginx -s reload
log_info "Nginx 配置已更新并重载"

log_info "=== 6. 停止旧的活跃实例 ==="
docker-compose stop backend-$ACTIVE
docker-compose rm -f backend-$ACTIVE

log_info "=== 7. 更新前端（如有变化） ==="
docker-compose build frontend
docker-compose up -d frontend

log_info "=== 部署完成！当前活跃实例: $STANDBY ==="
log_info "访问地址: http://你的服务器IP"
