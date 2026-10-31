# 开发日志

> 每天三行：今天完成 / 明天计划 / 卡点。用于形成真实 Git 历史。

## 2026-11-01

**今天完成**
- 初始化仓库结构：`.gitignore`、`.env.example`、`README.md`、`requirements.txt`
- 服务端支持 `.env`，密钥优先读环境变量（`DEEPSEEK_API_KEY`），保留 `ai.json` 兼容回退
- 移除页脚真实电话与地址，避免个人信息进入公开仓库
- 新增核验 Agent：5 个工具（取物品/取申请/相似检索/举报/规则）、证据链、LLM 裁决 + 规则兜底
- 新增 RAG 问答：本地 BM25 检索 + 引用，零额外接口成本
- 新增 SSE 流式：`/api/agent/review/stream`（step / delta / done）
- 新增多模态接口 `/api/vision/analyze`，未配置密钥时优雅降级

**明天计划**
- 前端接入：核对面板显示 Agent 步骤时间线；首页问答入口
- 多模态接入发布页（上传照片自动填分类）

**卡点**
- 待替换大模型密钥；视觉模型账号待注册
