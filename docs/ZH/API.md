# API Guide

当前 SDK package 版本：`0.2.4`

Base path：`/api/v1/`

## 认证

Dashboard 用户使用 session 认证。服务端集成可以使用 service token：

```http
Authorization: Bearer zhlm_...
```

SDK 设备使用 activation token：

```http
Authorization: Bearer zhla_...
```

生成 service token：

```bash
.venv/bin/python manage.py issue_service_token --username admin --name zhl-robot-01
```

## SDK API Key

Dashboard 用户可以从左侧菜单 **API Keys** 创建 SDK API Key。每个用户可以给 key 命名、设置允许激活的设备数量、之后再次查看/复制完整 key，也可以删除不再使用的 key。

需要自动化或内部初始化时，也可以从服务器生成 SDK API Key：

```bash
.venv/bin/python manage.py issue_sdk_key --username zhl-lstm --name zhl-internal-memory-sdk
```

API Key 认证使用 prefix 和 SHA-256 hash。Dashboard 会保存 encrypted recoverable copy，方便 owner 之后再次查看自己的 key。

## Health

```http
GET /api/v1/health/
```

## 激活 SDK 设备

```http
POST /api/v1/sdk/activate/
Content-Type: application/json
```

```json
{
  "api_key": "zhlsk_...",
  "device_id": "robot-serial-001",
  "device_name": "Robot 001",
  "sdk_version": "0.2.4",
  "platform": "linux"
}
```

响应会返回 `activation_token`，之后用它作为 `Bearer` auth。

## 分析记忆

Analyze 会提取 facts 和候选 memories，但不会写入数据库。

```http
POST /api/v1/memories/analyze/
Authorization: Bearer zhla_...
Content-Type: application/json
```

```json
{
  "conversation_text": "My name is Sara. My favorite color is blue.",
  "language": "en"
}
```

## 写入记忆

Ingest 会把 memory records 和 current facts 写入当前认证 owner 的私有 vault。

```http
POST /api/v1/memories/ingest/
Authorization: Bearer zhla_...
Content-Type: application/json
```

```json
{
  "conversation_text": "My name is Sara. I love blue.",
  "source_channel": "robot_chat",
  "language": "en",
  "facts": [
    {
      "key": "first_name",
      "value": "Sara",
      "category": "identity",
      "sensitivity": "private",
      "confidence": 0.94
    }
  ]
}
```

## 搜索记忆

```http
GET /api/v1/memories/search/?q=blue&category=preference&limit=25
Authorization: Bearer zhla_...
```

Search 始终只查询当前认证 owner 的数据。

## 当前 Facts

```http
GET /api/v1/memories/facts/?key=favorite_color
Authorization: Bearer zhla_...
```

## RAG Context

云端平台 `0.2.8` 增加了 owner-scoped context endpoint，用于聊天模型集成。它会返回 current facts、相关 memories，以及可以发送给 OpenAI-compatible 或私有聊天模型的 `prompt_context` 字符串。

```http
POST /api/v1/memories/rag-context/
Authorization: Bearer zhla_...
Content-Type: application/json

{
  "query": "favorite color and bedtime story preferences",
  "limit": 8,
  "include_facts": true
}
```

RAG 召回始终先按当前认证 owner 过滤，然后再做记忆搜索。

## 内容库

```http
GET /api/v1/content/library/?type=story&language=en
Authorization: Bearer zhla_...
```

## Sandbox 与本地 SDK

Dashboard Sandbox 是 UI 测试界面。开发者可以像普通聊天一样测试，只有检测到值得记住的信息时 Live memory JSON 才会更新，并且可以在机器人集成前验证冲突处理行为。

Sandbox 记忆只是临时测试状态。它保存在当前页面会话中，刷新 Sandbox 页面后会重置。

机器人端如果需要与 Sandbox 一致的行为，应先使用 `zhl_memory_core` 的 `MemoryManager`，再调用云端 ingest。直接调用 API ingest 会保存提交的 payload；本地 manager 负责在同步前进行本地冲突确认。
