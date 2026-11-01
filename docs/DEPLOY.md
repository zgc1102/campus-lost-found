# 部署到云服务器（Ubuntu 22.04）

目标：手机流量能打开 `https://你的域名`，评审期不掉线。

---

## 一、买服务器（10 分钟）

推荐：腾讯云轻量应用服务器 / 阿里云轻量。

| 选项 | 选择 |
|---|---|
| 地域 | **中国香港** 或 **新加坡**（免备案） |
| 镜像 | Ubuntu 22.04 LTS |
| 套餐 | 2 核 2G，3M 带宽 |
| 时长 | 1 年，关闭自动续费 |
| 登录 | 设置 root 密码，记下来 |

买完记下：**公网 IP**、**root 密码**。

> 为什么选香港：大陆服务器绑定域名要 ICP 备案，1–3 周，来不及。

---

## 二、买域名并解析（10 分钟）

1. 腾讯云/阿里云 → 域名注册 → 搜 `shiguangli.top` 之类，首年 10–30 元
2. 实名认证（1–3 天）
3. 域名解析 → 添加两条 A 记录：

```
@    A    你的服务器IP
www  A    你的服务器IP
```

4. 等 10 分钟，`ping 你的域名` 能看到 IP

---

## 三、上传代码（二选一）

**方式 A：从 GitHub 拉（推荐）**

```bash
ssh root@你的IP
apt update && apt install -y git
git clone https://github.com/zgc1102/campus-lost-found.git /opt/lostfound
```

**方式 B：本地上传**

```powershell
scp -r "D:\Users\周冠晨\Desktop\拾光里共享版" root@你的IP:/opt/lostfound
```

---

## 四、一键部署

把 `scripts/` 目录一起传上去，然后：

```bash
cd /opt/lostfound
bash scripts/deploy.sh 你的域名
```

脚本会做：

1. 安装 Python、Caddy
2. 创建虚拟环境（本项目无第三方依赖，纯标准库）
3. 写入 systemd 服务并开机自启
4. 写入 Caddy 配置并自动申请 HTTPS 证书
5. 配置每日备份（保留 7 天）

> 部署前先把 `.env` 放到 `/opt/lostfound/.env`（内容见 `.env.example`），否则 AI 功能不可用。

---

## 五、验收（必须逐条过）

```bash
# 1. 服务状态
systemctl status lostfound --no-pager

# 2. 本机探活
curl http://127.0.0.1:8000/api/ping

# 3. 公网探活
curl https://你的域名/api/ping
```

手机验收：

- [ ] 关掉 Wi-Fi，用流量打开 `https://你的域名`
- [ ] 地址栏有小锁
- [ ] 能发布一条、能看到列表
- [ ] `https://你的域名/admin` 能登录
- [ ] 重启服务器后 5 分钟内自动恢复

---

## 六、加 CDN（Cloudflare，免费，10 分钟）

目的：1 万人同时打开时，静态资源走 CDN，源站压力降到 1/10。

1. 注册 <https://dash.cloudflare.com> → Add a site → 输入域名 → 选 Free
2. Cloudflare 会给两个 NS 地址，去域名商后台把 NS 改成这两个
3. 等生效（几分钟到几小时），状态变 Active
4. SSL/TLS → Overview → 选 **Full (strict)**
5. Rules → Cache Rules，加三条：

| 路径 | 规则 |
|---|---|
| `/assets/*` | Cache everything，Edge TTL 1 年 |
| `/`、`/admin`、`/*.html` | Bypass cache |
| `/api/*` | Bypass cache（接口自己带 ETag） |

6. 再跑一次压测对比：

```bash
python scripts/loadtest.py --base https://你的域名 --path / --requests 10000 --concurrency 500
```

## 七、压测

```bash
python scripts/loadtest.py --base https://你的域名 --path / --requests 10000 --concurrency 500
```

结果填进 `docs/LOADTEST.md` 的表格，答辩时直接展示。

## 八、监控与备份

**监控**：<https://uptimerobot.com/> → Add New Monitor → HTTP(s) → `https://你的域名/api/ping` → 5 分钟。

**备份**：脚本已配置 cron，每天 03:00 打包到 `/var/backups/lostfound`，保留 7 天。

手动恢复：

```bash
tar xzf /var/backups/lostfound/xxx.tar.gz -C /opt/lostfound
systemctl restart lostfound
```

---

## 九、常见问题

| 现象 | 原因 | 解决 |
|---|---|---|
| `curl` 502 | 服务没起来 | `journalctl -u lostfound -n 50` |
| 证书申请失败 | 域名没解析或 80 端口被挡 | 检查 DNS、`ufw status` |
| 页面能开但接口 404 | 反向代理路径错 | 检查 Caddyfile |
| AI 不工作 | `.env` 没放或 key 错 | `cat /opt/lostfound/.env` |
| 手机打不开 | 安全组没开 443 | 云控制台放行 80/443 |

---

## 十、更新代码

```bash
cd /opt/lostfound
git pull
systemctl restart lostfound
```
