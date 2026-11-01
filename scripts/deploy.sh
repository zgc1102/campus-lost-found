#!/usr/bin/env bash
# 一键部署：bash scripts/deploy.sh 你的域名
set -e

DOMAIN="${1:-}"
if [ -z "$DOMAIN" ]; then
  echo "用法：bash scripts/deploy.sh 你的域名"
  exit 1
fi

APP_DIR="/opt/lostfound"
if [ "$(pwd)" != "$APP_DIR" ]; then
  APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
fi
echo "== 部署目录：$APP_DIR =="
echo "== 域名：$DOMAIN =="

echo "== 1/6 安装依赖 =="
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y python3 python3-venv curl ufw debian-keyring debian-archive-keyring apt-transport-https

if ! command -v caddy >/dev/null 2>&1; then
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' > /etc/apt/sources.list.d/caddy-stable.list
  apt-get update -y
  apt-get install -y caddy
fi

echo "== 2/6 虚拟环境 =="
cd "$APP_DIR"
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip -q
if [ -f requirements.txt ]; then pip install -r requirements.txt -q || true; fi

echo "== 3/6 systemd 服务 =="
cat > /etc/systemd/system/lostfound.service <<EOF
[Unit]
Description=Shiguangli Lost and Found
After=network.target

[Service]
WorkingDirectory=$APP_DIR
EnvironmentFile=-$APP_DIR/.env
ExecStart=$APP_DIR/.venv/bin/python server.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable lostfound
systemctl restart lostfound

echo "== 4/6 Caddy：静态直出 + API 反代 =="
cat > /etc/caddy/Caddyfile <<EOF
$DOMAIN, www.$DOMAIN {
    encode gzip zstd
    root * $APP_DIR

    # 接口走 Python
    @api path /api/*
    handle @api {
        reverse_proxy 127.0.0.1:8000
    }

    # 静态资源长缓存（文件名不变时一年）
    @assets path /assets/*
    header @assets Cache-Control "public, max-age=31536000, immutable"

    # 页面不缓存，保证更新立即生效
    @pages path / /用户端.html /管理端.html /admin
    header @pages Cache-Control "no-cache"

    rewrite / /用户端.html
    rewrite /admin /管理端.html
    file_server
}
EOF
systemctl restart caddy

echo "== 5/6 防火墙 =="
ufw allow 22/tcp || true
ufw allow 80/tcp || true
ufw allow 443/tcp || true
yes | ufw enable || true

echo "== 6/6 备份 =="
mkdir -p /var/backups/lostfound
cat > /usr/local/bin/lostfound-backup.sh <<EOF
#!/usr/bin/env bash
cd $APP_DIR
tar czf /var/backups/lostfound/lostfound-\$(date +%F-%H%M).tar.gz \\
  items.json claims.json notices.json accounts.json announcements.json ai.json 2>/dev/null || true
find /var/backups/lostfound -name '*.tar.gz' -mtime +7 -delete
EOF
chmod +x /usr/local/bin/lostfound-backup.sh
(crontab -l 2>/dev/null; echo "0 3 * * * /usr/local/bin/lostfound-backup.sh") | sort -u | crontab -

echo
echo "== 完成 =="
systemctl status lostfound --no-pager | head -n 12
echo
echo "验收：curl https://$DOMAIN/api/ping"
echo "如果失败：journalctl -u lostfound -n 50"
