# 安全事件处置清单（P0）

> 这份清单是应急操作，不替代代码审查。不要把真实 Key、管理员密码写进文档或聊天。

## 已经确认的问题

1. 静态文件暴露：
   - `/server.py`
   - `/items.json`
   - `/claims.json`
   - `/notices.json`
   - `/accounts.json`
   - `/risk_profiles.json`
   - `/moderation_reports.json`
   - `/chat_guard_alerts.json`
   - `/appeals.json`
   - `/docs/...`
   - `/private/...`
2. 管理员密码文件 `管理员密码.txt` 曾在 Web 根目录。
3. `/api/admin/ai/test` 曾允许把已保存的 Key 发到请求方指定的 base_url。
4. `/api/ask`、`/api/ask/stream`、`/api/vision/analyze`、`/api/agent/*`、`/api/precheck` 原本无鉴权、无限流。
5. 已部署代码：
   - 私密文件迁到 `private/`
   - 静态文件只允许 `/web/`、`/map/` 和根目录三个 HTML
   - AI 接口加设备标识 + 每日预算 + 单 IP 限流
   - 管理端测试接口禁止把已有 Key 发到新地址
   - 管理端登录失败限流

## 仍然必须在 Nginx / Cloudflare 做

代码只能管住 Python 的静态文件回退。  
如果 Nginx 直接返回项目根目录文件，必须改 Nginx。

```nginx
# 禁止根目录源码、数据、文档
location ~* \.(env|json|py|md|txt|bak|log|sql)$ {
    deny all;
}

location ^~ /docs/ {
    deny all;
}

location ^~ /private/ {
    deny all;
}

# 管理端接口先限制来源 IP；确认后再放开
location ^~ /api/admin/ {
    allow 你的公网IP;
    deny all;
}
```

注意：把这段放进现有 `server {}`，不要覆盖原来的 `/api/` 反代配置。  
如果 `/api/admin/` 被 `deny all` 挡住，管理端会暂时不可用，这是应急预期。

## Cloudflare

1. Caching → Configuration → Purge Everything
2. 至少单独 purge：
   - `/管理员密码.txt`
   - `/ai.json`
   - `/server.py`
   - `/items.json`
   - `/accounts.json`
3. 加 WAF 速率限制：
   - `/api/ask`：10 次/分钟/IP
   - `/api/vision/analyze`：5 次/分钟/IP
   - `/api/admin/*`：只允许自己的 IP

## 模型平台

1. 作废旧 Key：
   - `DEEPSEEK_API_KEY`
   - `VISION_API_KEY`
   - `REPORT_AI_API_KEY`
2. 新建 Key，只写服务器 `.env`
3. 设置每日/每月消费上限和余额告警
4. 查用量日志：调用时间、模型、IP/来源、是否集中在 `/api/ask`

## 管理员

1. 修改 `/opt/lostfound/private/admin.json` 里的 password
2. 删除 `/opt/lostfound/private/管理员密码.txt`
3. 重启 `lostfound`，使旧管理员 token 全部失效
4. 不要把新密码写进 README、docs、网盘、截图

## 数据

`/accounts.json` 曾暴露手机号、salt、hash。  
`/claims.json`、`/notices.json`、`/chat_guard_alerts.json` 曾暴露业务数据。

需要：

1. 备份后清理测试账号数据
2. 通知真实用户（如果有）
3. 评估是否需要强制重置密码
4. 不要把生产数据放进公开仓库或网盘

## 验证

```bash
curl -I https://shiguangli.work/server.py
curl -I https://shiguangli.work/items.json
curl -I https://shiguangli.work/accounts.json
curl -I https://shiguangli.work/管理员密码.txt
curl -I https://shiguangli.work/docs/TEST-ACCOUNTS.md
```

预期全部 `403` 或 `404`。

```bash
curl -X POST https://shiguangli.work/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"test"}'
```

预期 `401`，不是 `200`。

## 重要提醒

已经提交的比赛版本和现在 GitHub 的 `main` 可能已经不一致。  
如果提交入口还能修改，应把安全修复、网盘包、技术文档一起更新；  
如果已经锁定，先问组委会是否允许安全修复，不要单方面替换已提交材料。
