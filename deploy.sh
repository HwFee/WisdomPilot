#!/bin/bash
# ============================================
# 智码领航 - 一键部署脚本
# 本地构建 → 上传服务器 → 远程部署
# ============================================

set -e

# ---------- 配置区（请按需修改） ----------
SERVER_IP="115.175.38.106"
SSH_USER="root"                 # 必填：SSH 用户名，如 root 或 ubuntu
SSH_PORT=22                 # SSH 端口
SSH_KEY=""                  # 可选：SSH 私钥路径，如 ~/.ssh/id_rsa

# 前端 API 地址（部署后浏览器访问的地址）
NEXT_PUBLIC_API_URL="http://${SERVER_IP}:8000"

# 镜像名称
BACKEND_IMAGE="aicodingteach-backend"
FRONTEND_IMAGE="aicodingteach-frontend"
BACKEND_TAG="latest"
FRONTEND_TAG="latest"

# 服务器上存放部署文件的目录（与现有部署目录一致）
REMOTE_DEPLOY_DIR="/opt/ai-teach"

# 后端暴露端口
BACKEND_PORT=8000
FRONTEND_PORT=3000

# 本地环境变量文件路径（相对项目根目录）
BACKEND_ENV="backend/.env"
# ------------------------------------------

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC}  $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ---------- 前置检查 ----------
if [ -z "$SSH_USER" ]; then
    log_error "请先在脚本中设置 SSH_USER（SSH 用户名）"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    log_error "本地未找到 docker 命令，请先安装 Docker"
    exit 1
fi

if ! command -v ssh &> /dev/null || ! command -v scp &> /dev/null; then
    log_error "本地未找到 ssh/scp 命令"
    exit 1
fi

# 组装 SSH/SCP 参数
SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
if [ -n "$SSH_KEY" ]; then
    SSH_OPTS="${SSH_OPTS} -i ${SSH_KEY}"
fi

SSH_CMD="ssh ${SSH_OPTS} -p ${SSH_PORT} ${SSH_USER}@${SERVER_IP}"
SCP_CMD="scp ${SSH_OPTS} -P ${SSH_PORT}"

# ---------- 1. 本地构建镜像 ----------
log_info "开始本地构建镜像..."
log_info "前端构建参数 NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}"

cd "$(dirname "$0")"
PROJECT_ROOT=$(pwd)

# 构建后端
cd "${PROJECT_ROOT}/backend"
log_info "构建后端镜像 ${BACKEND_IMAGE}:${BACKEND_TAG} ..."
docker build -t "${BACKEND_IMAGE}:${BACKEND_TAG}" .

# 构建前端
cd "${PROJECT_ROOT}/frontend"
log_info "构建前端镜像 ${FRONTEND_IMAGE}:${FRONTEND_TAG} ..."
docker build --build-arg NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL}" -t "${FRONTEND_IMAGE}:${FRONTEND_TAG}" .

cd "${PROJECT_ROOT}"

# ---------- 2. 保存镜像 ----------
log_info "保存镜像到本地..."
BACKEND_TAR="/tmp/${BACKEND_IMAGE}.tar"
FRONTEND_TAR="/tmp/${FRONTEND_IMAGE}.tar"

docker save "${BACKEND_IMAGE}:${BACKEND_TAG}" -o "${BACKEND_TAR}"
docker save "${FRONTEND_IMAGE}:${FRONTEND_TAG}" -o "${FRONTEND_TAR}"

log_info "镜像已保存:"
ls -lh "${BACKEND_TAR}" "${FRONTEND_TAR}"

# ---------- 3. 上传文件到服务器 ----------
log_info "上传部署文件到服务器 ${SERVER_IP} ..."

# 创建远程目录
${SSH_CMD} "mkdir -p ${REMOTE_DEPLOY_DIR}/data"

# 上传镜像
${SCP_CMD} "${BACKEND_TAR}" "${SSH_USER}@${SERVER_IP}:${REMOTE_DEPLOY_DIR}/"
${SCP_CMD} "${FRONTEND_TAR}" "${SSH_USER}@${SERVER_IP}:${REMOTE_DEPLOY_DIR}/"

# 上传数据文件（backend/data.db 才是真正的数据库）
DB_FILE="${PROJECT_ROOT}/backend/data.db"
if [ -f "${DB_FILE}" ]; then
    log_info "删除服务器上旧的数据库文件..."
    ${SSH_CMD} "rm -f ${REMOTE_DEPLOY_DIR}/data/data.db ${REMOTE_DEPLOY_DIR}/data/data.db-shm ${REMOTE_DEPLOY_DIR}/data/data.db-wal"

    log_info "上传数据库文件 ..."
    ${SCP_CMD} "${DB_FILE}" "${SSH_USER}@${SERVER_IP}:${REMOTE_DEPLOY_DIR}/data/"
    # WAL 模式下的附加文件也一并上传，避免数据丢失
    if [ -f "${DB_FILE}-shm" ]; then
        ${SCP_CMD} "${DB_FILE}-shm" "${SSH_USER}@${SERVER_IP}:${REMOTE_DEPLOY_DIR}/data/"
    fi
    if [ -f "${DB_FILE}-wal" ]; then
        ${SCP_CMD} "${DB_FILE}-wal" "${SSH_USER}@${SERVER_IP}:${REMOTE_DEPLOY_DIR}/data/"
    fi
else
    log_warn "未找到 ${DB_FILE}，跳过上传数据库"
fi

# 上传环境变量文件（如果存在）
if [ -f "${PROJECT_ROOT}/${BACKEND_ENV}" ]; then
    log_info "上传后端环境变量文件 ..."
    ${SCP_CMD} "${PROJECT_ROOT}/${BACKEND_ENV}" "${SSH_USER}@${SERVER_IP}:${REMOTE_DEPLOY_DIR}/.env"
else
    log_warn "未找到 ${BACKEND_ENV}，请确保服务器上已配置环境变量"
fi

# ---------- 4. 服务器端部署 ----------
log_info "在服务器上执行部署..."

${SSH_CMD} << EOF
set -e

echo "[远程] 加载后端镜像..."
docker load -i ${REMOTE_DEPLOY_DIR}/${BACKEND_IMAGE}.tar

echo "[远程] 加载前端镜像..."
docker load -i ${REMOTE_DEPLOY_DIR}/${FRONTEND_IMAGE}.tar

echo "[远程] 停止并删除旧容器..."
docker stop ${BACKEND_IMAGE} 2>/dev/null || true
docker rm ${BACKEND_IMAGE} 2>/dev/null || true
docker stop ${FRONTEND_IMAGE} 2>/dev/null || true
docker rm ${FRONTEND_IMAGE} 2>/dev/null || true

echo "[远程] 启动后端容器..."
docker run -d \
    --name ${BACKEND_IMAGE} \
    --restart unless-stopped \
    -p ${BACKEND_PORT}:8000 \
    -v ${REMOTE_DEPLOY_DIR}/data:/app/data \
    -v ${REMOTE_DEPLOY_DIR}/.env:/app/.env:ro \
    -e DATABASE_URL="sqlite+aiosqlite:///./data/data.db" \
    ${BACKEND_IMAGE}:${BACKEND_TAG}

echo "[远程] 启动前端容器..."
docker run -d \
    --name ${FRONTEND_IMAGE} \
    --restart unless-stopped \
    -p ${FRONTEND_PORT}:3000 \
    ${FRONTEND_IMAGE}:${FRONTEND_TAG}

echo "[远程] 清理镜像文件..."
rm -f ${REMOTE_DEPLOY_DIR}/${BACKEND_IMAGE}.tar
rm -f ${REMOTE_DEPLOY_DIR}/${FRONTEND_IMAGE}.tar

echo "[远程] 当前运行容器:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
EOF

# ---------- 5. 本地清理 ----------
log_info "清理本地临时文件..."
rm -f "${BACKEND_TAR}" "${FRONTEND_TAR}"

log_info "部署完成！"
echo ""
echo "  前端地址: http://${SERVER_IP}:${FRONTEND_PORT}"
echo "  后端地址: http://${SERVER_IP}:${BACKEND_PORT}"
echo ""
log_info "如需查看远程日志，请执行:"
echo "  ${SSH_CMD} \"docker logs -f ${BACKEND_IMAGE}\""
echo "  ${SSH_CMD} \"docker logs -f ${FRONTEND_IMAGE}\""
