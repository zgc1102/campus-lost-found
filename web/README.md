# 拾光里 Web（Vue 3 + Vite）

这是拾光里从原生 HTML/CSS/JS 迁移到 Vue 3 的第一阶段：**首页已迁移，其余页面暂时跳回旧版**，用于保证功能不丢。

## 开发

```bash
pnpm install
pnpm dev
```

打开 `http://127.0.0.1:5173/`。

`/api` 已代理到现有 Python 后端 `http://127.0.0.1:8000`，不要另写一套后端。

## 构建

```bash
pnpm build
```

产物在 `dist/`。

## 当前迁移范围

- 首页：Vue 组件
- 顶部播报：保留原来的完整文案
- 数据：`/api/items`、`/api/announcements`
- 失物 / 寻物 / 互助 / 我的 / 拾光码 / 侦探：暂时跳回旧版 `用户端.html`

## 下一阶段

1. 迁失物 / 寻物列表
2. 迁发布表单
3. 迁雷达 / 侦探
4. 迁拾光码
5. 通过后部署到 `shiguangli.work`，旧版保留回退

## 注意

- 不要在前端写 API Key
- `node_modules/`、`dist/`、运行数据不进 Git
- 老版本 `用户端.html` 在迁移完成前不要删
