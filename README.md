# 拾光里 · 校园失物招领平台

面向高校场景的失物招领 Web 应用：大模型自动审核内容、自动匹配寻物与招领、用 AI 协助核对认领，
让「丢了东西」和「捡到东西」在几分钟内对上。

> 全国高校 AI Web 开发挑战赛 · B 组参赛作品

---

## 1. 它解决什么问题

- 校园失物信息散落在微信群、朋友圈，刷屏快、留存差，真正丢东西的人看不到；
- 公益平台没有值班人员，人工审核不可持续；
- 关键词过滤挡不住拼音、英文、谐音、拆字等规避写法；
- 失主不知道该描述什么，捡到的人不知道该问什么；
- 公开手机号容易被骚扰。

---

## 2. 核心功能

### 用户端

- 发布寻物 / 招领启事：分类、地点、时间、图片、独有特征
- AI 自动审核：通过即上架，不通过给原因并支持修改重提
- 相似物品自动匹配：寻物 ↔ 招领双向比对，双方收到通知
- 认领申请与核对：
  - 招领帖：失主填写「只有失主知道的特征」
  - 寻物帖：捡到的人填写「在哪捡到、什么时候」
- 通知中心、我的发布、账号登录（手机号 + 密码）
- 隐私保护：公开页手机号打码，认领通过后才交换完整号码

### 管理端

- 独立页面、密码登录、令牌鉴权
- 内容审核：通过 / 下架 / 驳回并填写理由
- AI 判定展示：风险分、理由、一键采纳或重新审核
- AI 配置：接口地址、模型、密钥、阈值、连通性测试
- 注册用户列表：手机号、注册时间、最近登录、发布数量

---

## 3. AI 能力

| 能力 | 状态 | 说明 |
|---|---|---|
| 内容审核 | ✅ 已上线 | 语义审核 + 二元终审 + 分数归一化 + 范围拦截 |
| 反规避 | ✅ 已上线 | 拼音、英文、谐音、拆字、跨行断句 |
| 类型识别 | ✅ 已上线 | 判断更像寻物还是招领，发布前提醒 |
| 核验 Agent | ✅ 已上线 | 5 个工具、证据链、LLM 裁决 + 规则兜底 |
| RAG 知识库 | ✅ 已上线 | 本地 BM25 检索 + 引用来源，零额外接口成本 |
| 多模态 | 🟡 接口就绪 | `/api/vision/analyze` 已实现，配置 `VISION_API_KEY` 后启用 |
| 流式交互 | ✅ 已上线 | `/api/agent/review/stream` SSE：step / delta / done |

---

## 4. 系统架构

```
浏览器（手机 / PC）
      │  HTTPS
      ▼
反向代理（Caddy，自动 HTTPS）
      │
      ▼
Python 服务（标准库 ThreadingHTTPServer）
      ├─ /api/items        发布 / 列表
      ├─ /api/precheck     发布前 AI 预检
      ├─ /api/claims       认领申请与核对
      ├─ /api/notices      通知
      ├─ /api/account      账号
      └─ /api/admin        管理端
      │
      ├─ 数据：JSON 文件（items / claims / notices / accounts）
      └─ AI：DeepSeek（审核、Agent、RAG 生成）
             └─ 视觉模型（图片理解）
```

---

## 5. 目录结构

```
campus-lost-found/
├─ README.md
├─ .env.example
├─ .gitignore
├─ requirements.txt
├─ server.py            # 服务端与接口
├─ 用户端.html           # 用户端页面结构
├─ 管理端.html           # 管理端页面结构
├─ assets/
│  ├─ styles.css        # 用户端样式
│  ├─ app.js            # 用户端逻辑
│  ├─ admin.css         # 管理端样式
│  └─ admin.js          # 管理端逻辑
├─ data/kb/             # RAG 知识库
├─ 公网启动器.py         # 本机启动 + 公网隧道
├─ docs/
│  ├─ PROGRESS.md       # 开发日志
│  └─ ARCHITECTURE.md   # 架构说明（待补）
└─ 使用说明.md
```

---

## 6. 快速开始（Windows）

### 6.1 准备

- Python 3.9+（安装时勾选 Add to PATH）
- 可选：cloudflared（需要公网访问时）

### 6.2 配置

```bash
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY
```

### 6.3 启动

```bash
python server.py
```

打开 <http://127.0.0.1:8000>，管理端 <http://127.0.0.1:8000/admin>。

首次启动会在 `admin.json` 生成管理员密码，并写入 `管理员密码.txt`。

### 6.4 公网访问（可选）

```bash
python 公网启动器.py
```

会启动服务、建立 Cloudflare 隧道，并在桌面生成「用户端 / 管理端」快捷方式与二维码页面。

---

## 7. 环境变量

| 变量 | 必填 | 说明 |
|---|---|---|
| `DEEPSEEK_API_KEY` | 是 | 大模型密钥，只放本机 `.env` |
| `DEEPSEEK_BASE_URL` | 否 | 默认 `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | 否 | 默认 `deepseek-chat` |
| `AI_ENABLED` | 否 | `1` 开启审核，`0` 关闭 |
| `VISION_API_KEY` | 否 | 多模态视觉模型密钥 |
| `VISION_MODEL` | 否 | 例如 `glm-4v-flash` |
| `PORT` | 否 | 默认 8000 |

> 仓库中不包含任何密钥；`.env`、`ai.json`、`accounts.json` 等已在 `.gitignore` 中排除。

---

## 8. 接口一览

| 接口 | 方法 | 说明 |
|---|---|---|
| `/api/items` | GET / POST | 列表 / 发布 |
| `/api/items/<id>` | PATCH / DELETE | 修改（自动重审）/ 删除 |
| `/api/items/<id>/claims` | POST | 申请认领 |
| `/api/claims` | GET | 收到的 / 发出的申请 |
| `/api/claims/<id>` | PATCH | 通过 / 拒绝 / 要求补充 |
| `/api/claims/<id>/complete` | POST | 完成归还 |
| `/api/notices` | GET | 通知 |
| `/api/account/login` | POST | 登录 / 注册 |
| `/api/precheck` | POST | 发布前 AI 预检 |
| `/api/agent/review` | POST | 核验 Agent：5 个工具 + 证据链 |
| `/api/agent/review/stream` | POST(SSE) | Agent 流式步骤与结论 |
| `/api/ask` | POST | RAG 校园失物问答（带引用） |
| `/api/vision/analyze` | POST | 图片识别（需配置视觉模型） |
| `/api/format` | POST | AI 信息整理：摘要 + 精简描述 + 字段 |
| `/api/announcements` | GET | 已发布公告（首页轮播） |
| `/api/admin/announcements` | GET/POST | 公告管理：列表 / 新建 |
| `/api/admin/announcements/<id>` | PATCH/DELETE | 发布、下线、编辑、删除 |
| `/api/sync` | GET | 公开列表 + 我的发布 |
| `/api/admin/*` | - | 审核、AI 配置、用户 |

---

## 9. 测试

```bash
# 接口冒烟
python -m pytest tests/ -q        # 待补
```

当前已用手工与无头浏览器完成主链路测试（发布、审核、匹配、认领、账号、管理端）。

---

## 10. 部署

1. 服务器：Ubuntu 22.04，2 核 2G
2. 安装 Python 3.10+、Caddy
3. 拉取代码，创建 `.env`
4. systemd 守护 `server.py`
5. Caddy 反代并自动申请 HTTPS 证书

（详细脚本见 `docs/DEPLOY.md`，待补）

---

## 11. 团队

- 北京城市学院 · B 组
- 成员：（待填）
- 指导教师：（待填）

---

## 12. 路线图

- [x] 发布、审核、匹配、认领、通知、账号、管理端
- [ ] 核验 Agent（工具调用 + 证据链）
- [ ] RAG 校园知识库
- [ ] 多模态图片理解
- [ ] 流式 AI 交互
- [ ] React + TypeScript 前端
- [ ] 云端部署与监控

---

## 13. 声明

- 本项目为原创作品，未包装任何开源项目；
- 演示数据为虚构数据，不含真实用户信息；
- 第三方接口密钥仅保存在本机，不随仓库分发。
