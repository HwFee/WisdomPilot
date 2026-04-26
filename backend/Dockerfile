# ============================================
# 智码领航后端 - Dockerfile
# ============================================
# 基于 Python 3.11 slim 镜像
# ============================================

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖（使用清华镜像加速）
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制应用代码
COPY ./app ./app
COPY init_db.py .
COPY alembic.ini .
COPY ./migrations ./migrations

# 创建非 root 用户和数据目录
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --ingroup appgroup appuser && \
    mkdir -p /app/data /app/exercises && \
    chown -R appuser:appgroup /app

# 切换到非 root 用户
USER appuser

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
