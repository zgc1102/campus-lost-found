# 拾光里 MCP Server

`mcp_server.py` 把校园失物能力暴露成 MCP 工具，外部 Agent / IDE 可以直接调用。

## 启动

```bash
python mcp_server.py
```

使用 stdio JSON-RPC，一行一个消息。

## 工具

### search_lost_found

```json
{
  "name": "search_lost_found",
  "arguments": {
    "query": "黑色雨伞",
    "limit": 5
  }
}
```

返回公开的寻物 / 招领列表。

### get_tag

```json
{
  "name": "get_tag",
  "arguments": {
    "code": "SG2B9D96"
  }
}
```

返回拾光码、物品名、打码手机号、扫码链接；已注销返回 `deactivated: true`。

### campus_place_tips

```json
{
  "name": "campus_place_tips",
  "arguments": {
    "place": "图书馆"
  }
}
```

返回校园地点失物招领点建议。

## 协议验证

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
  | python mcp_server.py
```

## 比赛说明

- 这是标准 MCP stdio Server
- 工具直接读取本项目的 `items.json` / `tags.json`
- 不依赖云端，不暴露 API Key
- 外部 Agent 可以「查失物、查拾光码、问校园地点」
