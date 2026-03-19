# 部署指南

本文档介绍如何将 Skill Service 部署到生产环境。

## 📋 部署前准备

### 系统要求

- Python 3.8 或更高版本
- 至少 512MB RAM
- 至少 1GB 可用磁盘空间
- 网络连接（如果需要安装依赖）

### 依赖检查

```bash
# 检查 Python 版本
python --version

# 检查 pip 版本
pip --version
```

## 🚀 部署方式

### 方式 1: 使用 Docker（推荐）

#### 1. 创建 Dockerfile

在项目根目录创建 `Dockerfile`:

```dockerfile
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建日志目录
RUN mkdir -p logs

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "skill_service.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. 创建 docker-compose.yml

```yaml
version: '3.8'

services:
  skill-service:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./skills:/app/skills
      - ./logs:/app/logs
    environment:
      - SERVER_HOST=0.0.0.0
      - SERVER_PORT=8000
      - LOG_LEVEL=INFO
    restart: unless-stopped
```

#### 3. 构建和运行

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 方式 2: 使用 Systemd（Linux）

#### 1. 创建服务文件

创建 `/etc/systemd/system/skill-service.service`:

```ini
[Unit]
Description=Skill Service API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/skill-service
Environment="PATH=/var/www/skill-service/venv/bin"
ExecStart=/var/www/skill-service/venv/bin/uvicorn skill_service.api.server:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 2. 启动服务

```bash
# 重新加载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start skill-service

# 设置开机自启
sudo systemctl enable skill-service

# 查看状态
sudo systemctl status skill-service

# 查看日志
sudo journalctl -u skill-service -f
```

### 方式 3: 使用 Nginx 反向代理

#### 1. 配置 Nginx

创建 `/etc/nginx/sites-available/skill-service`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL 证书
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # 反向代理
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 2. 启用配置

```bash
# 创建符号链接
sudo ln -s /etc/nginx/sites-available/skill-service /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

### 方式 4: 使用 Supervisor

#### 1. 安装 Supervisor

```bash
sudo apt-get install supervisor
```

#### 2. 创建配置文件

创建 `/etc/supervisor/conf.d/skill-service.conf`:

```ini
[program:skill-service]
command=/var/www/skill-service/venv/bin/uvicorn skill_service.api.server:app --host 0.0.0.0 --port 8000
directory=/var/www/skill-service
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/skill-service.log
```

#### 3. 启动服务

```bash
# 重新加载配置
sudo supervisorctl reread

# 更新配置
sudo supervisorctl update

# 启动服务
sudo supervisorctl start skill-service

# 查看状态
sudo supervisorctl status skill-service
```

## 🔒 安全配置

### 1. 启用 API Key 认证

修改 `.env` 文件：

```bash
API_KEY=your-strong-secret-key-here
ENABLE_AUTH=true
```

### 2. 配置 CORS

在 `skill_service/api/server.py` 中限制允许的域名：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # 限制特定域名
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # 限制 HTTP 方法
    allow_headers=["Content-Type", "Authorization"],  # 限制请求头
)
```

### 3. 配置 HTTPS

使用 Let's Encrypt 获取免费 SSL 证书：

```bash
# 安装 certbot
sudo apt-get install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

### 4. 防火墙配置

```bash
# 允许 HTTP
sudo ufw allow 80/tcp

# 允许 HTTPS
sudo ufw allow 443/tcp

# 启用防火墙
sudo ufw enable
```

## 📊 监控和日志

### 1. 日志管理

配置日志轮转，创建 `/etc/logrotate.d/skill-service`:

```
/var/log/skill-service/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload skill-service > /dev/null 2>&1 || true
    endscript
}
```

### 2. 监控服务健康

创建健康检查脚本：

```bash
#!/bin/bash
# healthcheck.sh

HEALTH_URL="http://localhost:8000/health"

response=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $response -eq 200 ]; then
    echo "Service is healthy"
    exit 0
else
    echo "Service is unhealthy (HTTP $response)"
    exit 1
fi
```

设置定时任务：

```bash
# 编辑 crontab
crontab -e

# 每分钟检查一次
* * * * * /path/to/healthcheck.sh >> /var/log/skill-health.log 2>&1
```

### 3. 使用 Prometheus 监控

添加 Prometheus 中间件到 `skill_service/api/server.py`:

```python
from prometheus_fastapi_instrumentator import Instrumentator

# 在应用创建后
Instrumentator().instrument(app).expose(app)
```

## 🔄 持续集成/持续部署 (CI/CD)

### GitHub Actions 示例

创建 `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run tests
      run: pytest

    - name: Deploy to server
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.SERVER_HOST }}
        username: ${{ secrets.SERVER_USER }}
        key: ${{ secrets.SSH_KEY }}
        script: |
          cd /var/www/skill-service
          git pull origin main
          source venv/bin/activate
          pip install -r requirements.txt
          sudo systemctl restart skill-service
```

## 📈 性能优化

### 1. 使用 Gunicorn

```bash
pip install gunicorn

# 启动服务
gunicorn skill_service.api.server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### 2. 启用缓存

在 `skill_service/api/server.py` 中添加缓存：

```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

# 配置 Redis 缓存
@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
```

### 3. 数据库连接池

如果使用数据库，配置连接池：

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20
)
```

## 🐛 故障排除

### 问题 1: 服务无法启动

```bash
# 检查端口占用
sudo lsof -i :8000

# 检查日志
sudo journalctl -u skill-service -n 50

# 检查权限
ls -la /var/www/skill-service
```

### 问题 2: Skills 无法加载

```bash
# 检查 skills 目录权限
ls -la skills/

# 检查 SKILL.md 文件
cat skills/example/SKILL.md

# 重新加载 skills
curl -X POST http://localhost:8000/api/v1/skills/reload
```

### 问题 3: 性能问题

```bash
# 检查系统资源
htop

# 检查数据库连接
ps aux | grep python

# 查看慢查询
sudo tail -f /var/log/skill-service.log | grep "execution_time"
```

## 📞 获取帮助

如果遇到问题：

1. 查看日志文件
2. 检查配置文件
3. 查看文档和 FAQ
4. 提交 Issue 到 GitHub

祝部署顺利！🚀
