#!/usr/bin/env bash
# 在服务器上一键部署（阿里云命令助手执行）
set -e

APP=/opt/lostfound
REPO=https://github.com/zgc1102/campus-lost-found.git

echo "== 1/6 安装依赖 =="
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y git python3 nginx curl

echo "== 2/6 拉取代码 =="
if [ -d "$APP/.git" ]; then
  cd "$APP" && git pull --ff-only
else
  rm -rf "$APP"
  git clone --depth 1 "$REPO" "$APP"
fi
cd "$APP"

echo "== 3/6 写入配置 =="
if [ -n "$DEEPSEEK_API_KEY" ]; then
  cat > .env <<EOF
DEEPSEEK_API_KEY=$DEEPSEEK_API_KEY
DEEPSEEK_MODEL=${DEEPSEEK_MODEL:-deepseek-chat}
VISION_API_KEY=$VISION_API_KEY
VISION_MODEL=${VISION_MODEL:-glm-5.3-flash}
EOF
  chmod 600 .env
  echo "已写入 .env"
else
  echo "未提供 API Key，AI 功能将不可用（稍后可补 .env）"
fi

echo "== 4/6 systemd =="
cat > /etc/systemd/system/lostfound.service <<EOF
[Unit]
Description=Shiguangli Lost and Found
After=network.target

[Service]
WorkingDirectory=$APP
EnvironmentFile=-$APP/.env
Environment=SG_STARTUP_SKIP=1
ExecStart=/usr/bin/python3 server.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable lostfound
systemctl restart lostfound

echo "== 5/6 nginx =="
cat > /etc/nginx/sites-available/lostfound <<'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    root /opt/lostfound;
    index 用户端.html;

    gzip on;
    gzip_types text/plain text/css application/javascript application/json image/svg+xml;
    gzip_min_length 800;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 60s;
    }

    location /assets/ {
        expires 365d;
        add_header Cache-Control "public, immutable";
    }

    location = / {
        try_files /用户端.html =404;
        add_header Cache-Control "no-cache";
    }

    location = /admin {
        try_files /管理端.html =404;
        add_header Cache-Control "no-cache";
    }

    location / {
        try_files $uri $uri/ =404;
    }
}
EOF
ln -sf /etc/nginx/sites-available/lostfound /etc/nginx/sites-enabled/lostfound
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

echo "== 6/6 自检 =="
sleep 2
systemctl is-active lostfound || true
curl -s http://127.0.0.1:8000/api/health || true
echo
curl -s -o /dev/null -w "首页 HTTP %{http_code}\n" http://127.0.0.1/ || true
echo "== 完成 =="
