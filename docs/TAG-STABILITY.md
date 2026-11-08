# 拾光码长期有效性说明

## 对外承诺

拾光码默认**长期有效，不设自动过期时间**。

二维码里只保存：

```text
https://shiguangli.work/?tag=<CODE>
```

不保存版本号、时间戳、签名、页面路径。

## 为什么版本更新不会让码失效

- 二维码只依赖两个稳定要素：域名 `shiguangli.work` 和码值 `CODE`
- 网站更新只改前端页面和后端代码，不改域名、不改码值
- 扫码进入网站根路径，由前端识别 `?tag=CODE`
- 后端通过 `/api/tags/<CODE>` 查询 `tags.json`
- 部署脚本只执行 `git reset --hard`，不会删除未被 Git 跟踪的 `tags.json`
- 因此正常版本更新不会导致旧码失效

## 不能再改的契约

以下三项视为冻结契约，后续大版本更新必须保留：

1. 域名仍为 `https://shiguangli.work`
2. 扫码地址仍支持 `/?tag=<CODE>`
3. 查询接口仍为 `GET /api/tags/<CODE>`，通知接口仍为 `POST /api/tags/<CODE>/notify`

如果要改域名或路由，必须同时保留旧地址 301/302 跳转，至少保留一年。

## 数据保护

`tags.json` 是拾光码数据文件，不提交到 Git。

部署前备份：

```bash
cd /opt/lostfound
cp tags.json tags.json.bak.$(date +%Y%m%d)
```

迁移服务器时必须一起迁移：

- `tags.json`
- `items.json`
- `accounts.json`
- `notices.json`
- `.env`

## 有效期口径

对用户展示：

> 此码长期有效，不随网站版本更新失效。

不写“有效期一年”，避免用户每年重新打印。

只有在服务终止或域名变更时，才需要提前公告并保留旧地址跳转。

## 旧码说明

2026-11-08 之前生成的码指向：

```text
/拾光码.html?code=<CODE>
```

该路径在现 nginx 下不可用，旧码必须重新生成、重新打印。

2026-11-08 之后生成的码使用：

```text
/?tag=<CODE>
```

新码不受版本更新影响。
