# 智码领航 - 华为云部署指南（无域名版）

> 本文档描述如何在华为云服务器上部署智码领航系统，使用 IP 地址直接访问。

---

## 一、整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      用户请求                                │
│              http://你的服务器IP                             │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Nginx (80)                               │
│              蓝绿负载均衡 + 反向代理                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
┌───────────────────┐         ┌───────────────────┐
│  Backend-Green    │         │   Backend-Blue   │
│    (端口 8001)    │         │    (端口 8002)   │
│      主用实例      │         │      备用实例     │
└───────────────────┘         └───────────────────┘
            │                           │
            └─────────────┬─────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (3000)                          │
│                    Next.js 服务端渲染                        │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  SQLite 数据库 (持久化)                      │
│                  Docker Volume 挂载                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、部署前准备

### 2.1 前置条件

- ✅ 华为云 ECS 服务器（已购买）
- ✅ 公网 IP 地址（假设为 `123.45.67.89`，替换为你的实际 IP）
- ✅ 操作系统：Ubuntu 22.04 推荐
- ✅ 硅基流动 API Key（已有）

### 2.2 GitHub → Gitee 自动同步

解决华为云访问 GitHub 慢的问题：

#### 步骤 1：创建 Gitee 账号

1. 访问 https://gitee.com 注册账号
2. 设置 → 私人令牌 → 生成新令牌
   - 勾选权限：`projects`、`pull_requests`
   - 记下生成的令牌（只显示一次）

#### 步骤 2：在 GitHub 配置 Secrets

在你的 GitHub 仓库中：

1. 进入 `Settings` → `Secrets and variables` → `Actions`
2. 点击 `New repository secret`，添加：

| Name | Value |
|------|-------|
| `GITEE_TOKEN` | 你的 Gitee 私人令牌 |
| `GITEE_PRIVATE_KEY` | 服务器的 SSH 私钥（用于后续自动部署） |

#### 步骤 3：确认同步工作流

文件 `.github/workflows/sync-to-gitee.yml` 已配置好，每次推送到 main 分支会自动同步到 Gitee。

**你的 Gitee 仓库地址：** `https://gitee.com/dongyanchang/AlcodiingTeach-demo.git`

---

## 三、服务器初始化

### 3.1 登录服务器

```bash
# Windows 使用 PowerShell 或 SSH 客户端
ssh root@你的华为云公网IP

# 例如
ssh root@123.45.67.89
```

### 3.2 系统更新

```bash
# 更新软件包列表
apt update && apt upgrade -y

# 安装基础工具
apt install -y curl wget git vim
```

### 3.3 安装 Docker

```bash
# 安装 Docker
apt install -y docker.io docker-compose-v2

# 启动 Docker
systemctl enable docker
systemctl start docker

# 验证安装
docker --version
docker compose version
```

### 3.4 安装 Nginx

```bash
# 安装 Nginx
apt install -y nginx

# 启动 Nginx
systemctl enable nginx
systemctl start nginx

# 验证
nginx -v
```

### 3.5 配置华为云安全组

在华为云控制台 → ECS 实例 → 安全组，添加入方向规则：

| 端口 | 协议 | 源地址 | 说明 |
|------|------|--------|------|
| 22 | TCP | 0.0.0.0/0 | SSH 远程登录 |
| 80 | TCP | 0.0.0.0/0 | HTTP 网站访问 |
| 443 | TCP | 0.0.0.0/0 | HTTPS（可选） |

---

## 四、部署项目

### 4.1 克隆代码

```bash
# 创建项目目录
mkdir -p /opt/aicoding
cd /opt/aicoding

# 从 Gitee 克隆（国内速度快）
git clone https://gitee.com/dongyanchang/AlcodiingTeach-demo.git .

# 如果 Gitee 还没同步，暂时用 GitHub
# git clone https://github.com/HwFee/AlcodiingTeach-demo.git .
```

### 4.2 配置环境变量

```bash
cd /opt/aicoding

# 复制模板
cp .env.production .env

# 编辑配置
vim .env
```

**必须修改的配置：**

```env
# ============================================
# CORS 配置 - 替换为你的服务器 IP
# ============================================
CORS_ORIGINS=http://123.45.67.89,http://123.45.67.89:3000

# ============================================
# JWT 密钥 - 必须生成新的！
# ============================================
SECRET_KEY=这里填入生成的密钥

# ============================================
# AI 配置 - 填入你的硅基流动 API Key
# ============================================
AI_API_KEY=你的硅基流动API密钥
EMBEDDING_API_KEY=你的硅基流动API密钥
```

**生成 SECRET_KEY：**

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
# 复制输出结果到 .env 的 SECRET_KEY
```

### 4.3 配置 Nginx

```bash
# 复制 Nginx 配置
cp /opt/aicoding/nginx.conf /etc/nginx/conf.d/app.conf

# 删除默认站点配置
rm -f /etc/nginx/sites-enabled/default

# 测试配置语法
nginx -t

# 重载 Nginx
systemctl reload nginx
```

### 4.4 启动 Docker 服务

```bash
cd /opt/aicoding

# 创建数据目录
mkdir -p data

# 构建并启动所有服务
docker compose up -d --build

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f
```

### 4.5 验证部署

```bash
# 检查后端健康
curl http://127.0.0.1:8001/health
# 应返回: {"status":"healthy"}

# 检查前端
curl -I http://127.0.0.1:3000
# 应返回 200 OK
```

**浏览器访问：** `http://你的服务器IP`

---

## 五、前端配置

前端需要知道后端 API 地址，创建前端环境变量：

```bash
cd /opt/aicoding/frontend

# 创建 .env.local
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://123.45.67.89/api
EOF

# 替换 123.45.67.89 为你的实际 IP
```

然后重启前端：

```bash
cd /opt/aicoding
docker compose restart frontend
```

---

## 六、日常运维

### 6.1 更新代码

```bash
cd /opt/aicoding

# 拉取最新代码
git pull origin main

# 重新构建并部署
docker compose up -d --build

# 或者使用部署脚本（蓝绿部署）
chmod +x deploy.sh
./deploy.sh
```

### 6.2 查看日志

```bash
# 所有服务日志
docker compose logs -f

# 只看后端
docker compose logs -f backend-green

# 只看前端
docker compose logs -f frontend

# 最近 100 行
docker compose logs --tail=100 backend-green
```

### 6.3 重启服务

```bash
cd /opt/aicoding

# 重启后端
docker compose restart backend-green

# 重启前端
docker compose restart frontend

# 重启所有
docker compose restart
```

### 6.4 查看资源使用

```bash
# 容器资源使用
docker stats

# 磁盘使用
df -h

# 内存使用
free -h
```

### 6.5 进入容器调试

```bash
# 进入后端容器
docker exec -it backend-green bash

# 进入前端容器
docker exec -it frontend sh
```

---

## 七、数据备份

### 7.1 手动备份

```bash
# 创建备份目录
mkdir -p /opt/backups

# 备份数据库
cp /opt/aicoding/data/data.db /opt/backups/data_$(date +%Y%m%d).db

# 查看备份
ls -la /opt/backups/
```

### 7.2 自动备份（每天凌晨 3 点）

```bash
# 创建备份脚本
cat > /opt/backups/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
SOURCE="/opt/aicoding/data/data.db"
DEST="/opt/backups/data_$DATE.db"

if [ -f "$SOURCE" ]; then
    cp "$SOURCE" "$DEST"
    echo "[$(date)] Backup created: $DEST"
    # 保留最近 7 天的备份
    find /opt/backups -name "data_*.db" -mtime +7 -delete
else
    echo "[$(date)] Error: Database file not found"
fi
EOF

chmod +x /opt/backups/backup.sh

# 添加到 crontab
(crontab -l 2>/dev/null; echo "0 3 * * * /opt/backups/backup.sh >> /opt/backups/backup.log 2>&1") | crontab -

# 验证 crontab
crontab -l
```

---

## 八、故障排查

### 问题 1：后端无法启动

```bash
# 查看详细日志
docker compose logs backend-green

# 常见原因：
# 1. SECRET_KEY 未配置或太短
# 2. AI_API_KEY 未配置
# 3. 数据库文件权限问题

# 检查环境变量
docker exec backend-green env | grep -E "SECRET_KEY|AI_API_KEY"
```

### 问题 2：前端无法访问

```bash
# 检查前端容器
docker compose ps frontend

# 查看前端日志
docker compose logs frontend

# 检查前端环境变量
docker exec frontend cat /app/.next/standalone/.env.local
```

### 问题 3：API 请求跨域错误

```bash
# 检查 CORS 配置
cat /opt/aicoding/.env | grep CORS

# 确保包含你的访问地址
# CORS_ORIGINS=http://你的IP,http://你的IP:3000
```

### 问题 4：Nginx 502 错误

```bash
# 检查后端是否运行
curl http://127.0.0.1:8001/health

# 检查 Nginx 配置
nginx -t

# 查看 Nginx 错误日志
tail -f /var/log/nginx/error.log
```

### 问题 5：数据库连接失败

```bash
# 检查数据目录
ls -la /opt/aicoding/data/

# 修复权限（容器内使用 uid 1000）
chown -R 1000:1000 /opt/aicoding/data/
```

---

## 九、配置文件说明

| 文件 | 说明 |
|------|------|
| `docker-compose.yml` | Docker 编排配置，定义所有服务 |
| `backend/Dockerfile` | 后端 Python 镜像构建 |
| `frontend/Dockerfile` | 前端 Next.js 镜像构建 |
| `nginx.conf` | Nginx 反向代理 + 负载均衡 |
| `deploy.sh` | 蓝绿部署脚本 |
| `.env.production` | 生产环境变量模板 |
| `.env` | 实际环境变量（不提交到 Git） |

---

## 十、快速命令参考

```bash
# 部署
cd /opt/aicoding && docker compose up -d --build

# 查看状态
docker compose ps

# 查看日志
docker compose logs -f

# 重启
docker compose restart

# 停止
docker compose down

# 更新
git pull && docker compose up -d --build

# 备份
cp /opt/aicoding/data/data.db /opt/backups/data_$(date +%Y%m%d).db
```

---

## 十一、后续优化（可选）

### 11.1 配置域名（如果将来有域名）

1. 在域名服务商处添加 A 记录指向服务器 IP
2. 使用 Let's Encrypt 申请免费 SSL 证书：

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d your-domain.com
```

### 11.2 配置监控

```bash
# 安装 Node Exporter（Prometheus 采集器）
docker run -d --name=node-exporter \
  -p 9100:9100 \
  --restart=always \
  prom/node-exporter
```

---

*文档版本: v2.0（无域名版）*
*更新时间: 2026-04-23*
