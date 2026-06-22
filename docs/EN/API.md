# API Guide

Current SDK package version: `0.2.3`

Base path: `/api/v1/`

## Authentication

Dashboard users authenticate with their session. Service integrations can use service tokens:

```http
Authorization: Bearer zhlm_...
```

SDK devices use activation tokens:

```http
Authorization: Bearer zhla_...
```

Issue a service token:

```bash
.venv/bin/python manage.py issue_service_token --username admin --name zhl-robot-01
```

## SDK API Keys

Dashboard users can create SDK API keys from **API Keys** in the left sidebar. Each user can name a key, set the allowed device count, view/copy the full key later, and delete keys they no longer want to use.

Server-side automation can also issue an SDK API key:

```bash
.venv/bin/python manage.py issue_sdk_key --username zhl-lstm --name zhl-internal-memory-sdk
```

API key authentication uses a prefix and SHA-256 hash. The dashboard stores an encrypted recoverable copy so the owner can view the key again.

## Health

```http
GET /api/v1/health/
```

## Activate SDK Device

```http
POST /api/v1/sdk/activate/
Content-Type: application/json
```

```json
{
  "api_key": "zhlsk_...",
  "device_id": "robot-serial-001",
  "device_name": "Robot 001",
  "sdk_version": "0.2.3",
  "platform": "linux"
}
```

The response returns an `activation_token` that can be used as `Bearer` auth.

## Analyze Memory

Analyze extracts facts and candidate memories without writing to the database.

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

## Ingest Memory

Ingest writes memory records and current facts into the authenticated owner's private vault.

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

## Search Memories

```http
GET /api/v1/memories/search/?q=blue&category=preference&limit=25
Authorization: Bearer zhla_...
```

Search is always scoped to the authenticated owner.

## Current Facts

```http
GET /api/v1/memories/facts/?key=favorite_color
Authorization: Bearer zhla_...
```

## RAG Context

Cloud platform `0.2.7` adds an owner-scoped context endpoint for chat-model integrations. It returns current facts, relevant memories, and a `prompt_context` string that can be sent to an OpenAI-compatible or private chat model.

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

RAG retrieval is always scoped to the authenticated owner before memory search.

## Content Library

```http
GET /api/v1/content/library/?type=story&language=en
Authorization: Bearer zhla_...
```

## Sandbox And Local SDK

The dashboard Sandbox is a UI test surface. It lets developers chat normally, watch Live memory JSON update only when memory-worthy details are detected, and verify conflict behavior before integrating robots.

Sandbox memory is temporary test state. It is kept in the current page session and resets when the Sandbox page is refreshed.

For robot-side behavior that matches the Sandbox, use `MemoryManager` from `zhl_memory_core` before calling cloud ingest. Direct API ingest stores the submitted payload; the local manager is responsible for local conflict clarification before sync.
