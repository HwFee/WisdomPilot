# 智码领航 - 华为云部署指南

> 本文档描述如何在华为云服务器上部署智码领航系统，实现蓝绿部署和零停机更新。

---

## 一、整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      用户请求                                │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Nginx (80/443)                           │
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
└─────────────────────────────────────────────────────────────┘
```

---

## 二、部署前准备

### 2.1 配置 Gitee 自动同步

解决华为云访问 GitHub 慢的问题：

1. 登录 [Gitee](https://gitee.com)
2. 新建仓库 → 选择「从 GitHub 导入仓库」
3. 填入 GitHub 仓库地址：`https://github.com/HwFee/AI-Tutorial.git`
4. **勾选「自动同步」**
5. 记下 Gitee 仓库地址：`https://gitee.com/你的用户名/AI-Tutorial.git`

### 2.2 华为云服务器初始化

```bash
# 登录服务器
ssh root@你的华为云公网IP

# 更新系统
apt update && apt upgrade -y

# 安装 Docker
apt install docker.io docker-compose -y
systemctl enable docker
systemctl start docker

# 安装 Nginx
apt install nginx -y
systemctl enable nginx
systemctl start nginx

# 安装 Git
apt install git -y

# 创建项目目录
mkdir -p /opt/AI-Tutorial
cd /opt/AI-Tutorial

# 从 Gitee 克隆代码
git clone https://gitee.com/你的用户名/AI-Tutorial.git .
```

---

## 三、配置步骤

### 3.1 配置环境变量

```bash
cd /opt/AI-Tutorial

# 复制环境变量模板
cp .env.production .env

# 编辑环境变量
nano .env
```

**必须配置的变量：**

```env
# JWT 密钥（必须生成新的）
SECRET_KEY=使用下方命令生成

# AI API 密钥
AI_API_KEY=你的OpenAI密钥
MINIMAX_API_KEY=你的MiniMax密钥
EMBEDDING_API_KEY=你的硅基流动密钥
```

**生成 SECRET_KEY：**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3.2 配置 Nginx

```bash
# 复制 Nginx 配置
cp /opt/AI-Tutorial/nginx.conf /etc/nginx/conf.d/app.conf

# 删除默认配置
rm /etc/nginx/sites-enabled/default

# 测试配置
nginx -t

# 重载 Nginx
nginx -s reload
```

### 3.3 赋予部署脚本执行权限

```bash
chmod +x /opt/AI-Tutorial/deploy.sh
```

---

## 四、首次部署

```bash
cd /opt/AI-Tutorial

# 构建并启动所有服务
docker-compose up -d --build

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

**验证部署：**
- 后端健康检查：`curl http://127.0.0.1:8001/health`
- 前端访问：浏览器打开 `http://你的服务器IP`

---

## 五、日常更新流程

### 方式一：手动部署

```bash
cd /opt/AI-Tutorial
./deploy.sh
```

### 方式二：自动部署（Gitee Actions）

1. 进入 Gitee 仓库 → **管理** → **功能开关** → 开启 **Gitee Actions**
2. 进入 Gitee 仓库 → **管理** → **Secrets**，添加：
   - `SERVER_HOST`：华为云公网 IP
   - `SERVER_PRIVATE_KEY`：服务器 SSH 私钥

3. 之后每次推送到 main 分支，自动触发部署

---

## 六、常用运维命令

### 查看服务状态

```bash
docker-compose ps
docker-compose logs -f backend-green
docker-compose logs -f frontend
```

### 重启服务

```bash
# 重启后端
docker-compose restart backend-green

# 重启前端
docker-compose restart frontend

# 重启所有
docker-compose restart
```

### 查看资源使用

```bash
docker stats
```

### 进入容器调试

```bash
docker exec -it backend-green bash
```

---

## 七、蓝绿部署原理

```
部署前:
┌─────────────┐     ┌─────────────┐
│ Green (主)  │ ←── │   Nginx     │
│   8001      │     │             │
└─────────────┘     └─────────────┘
┌─────────────┐
│ Blue (备)   │
│   8002      │
└─────────────┘

部署中:
1. 构建新的 Blue 实例
2. 验证 Blue 健康
3. Nginx 切换到 Blue
4. 停止旧的 Green

部署后:
┌─────────────┐
│ Green (备)  │
│   8001      │
└─────────────┘
┌─────────────┐     ┌─────────────┐
│ Blue (主)   │ ←── │   Nginx     │
│   8002      │     │             │
└─────────────┘     └─────────────┘
```

**优点：**
- 零停机更新
- 快速回滚（切换回旧实例）
- 新版本验证后才切换流量

---

## 八、安全建议

### 8.1 华为云安全组配置

只开放必要端口：

| 端口 | 协议 | 说明 |
|------|------|------|
| 22 | TCP | SSH |
| 80 | TCP | HTTP |
| 443 | TCP | HTTPS |

### 8.2 配置 HTTPS（推荐）

使用 Let's Encrypt 免费证书：

```bash
# 安装 certbot
apt install certbot python3-certbot-nginx -y

# 申请证书
certbot --nginx -d 你的域名.com

# 自动续期
certbot renew --dry-run
```

### 8.3 数据备份

```bash
# 创建备份目录
mkdir -p /opt/backups

# 每日备份脚本
cat > /opt/backups/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d)
cp /opt/AI-Tutorial/data/data.db /opt/backups/data_$DATE.db
# 保留最近 7 天
find /opt/backups -name "data_*.db" -mtime +7 -delete
EOF

chmod +x /opt/backups/backup.sh

# 添加到 crontab（每天凌晨 3 点执行）
(crontab -l 2>/dev/null; echo "0 3 * * * /opt/backups/backup.sh") | crontab -
```

---

## 九、故障排查

### 后端无法启动

```bash
# 查看日志
docker-compose logs backend-green

# 常见问题：
# 1. SECRET_KEY 未配置
# 2. AI_API_KEY 未配置
# 3. 数据库文件权限问题
```

### 前端无法访问后端

```bash
# 检查 Nginx 配置
nginx -t

# 检查后端健康
curl http://127.0.0.1:8001/health

# 检查防火墙
ufw status
```

### 数据库连接失败

```bash
# 检查数据目录权限
ls -la /opt/AI-Tutorial/data/

# 修复权限
chown -R 1000:1000 /opt/AI-Tutorial/data/
```

---

## 十、配置文件清单

| 文件 | 说明 |
|------|------|
| `docker-compose.yml` | Docker 编排配置 |
| `backend/Dockerfile` | 后端镜像构建 |
| `frontend/Dockerfile` | 前端镜像构建 |
| `nginx.conf` | Nginx 反向代理配置 |
| `deploy.sh` | 一键部署脚本 |
| `.env.production` | 生产环境变量模板 |
| `.gitee/workflows/deploy.yml` | Gitee Actions 自动部署 |

---

*文档版本: v1.0*
*更新时间: 2026-04-23*
