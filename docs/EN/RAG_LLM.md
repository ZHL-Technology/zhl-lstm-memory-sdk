# RAG And LLM Integration Notes

Current SDK package version: `0.2.3`

## Scope

The public SDK is the robot-side memory core. It is not a trained LLM and it is not a full document RAG system by itself.

The SDK provides:

- local memory extraction with `MemoryEngine`
- local short-term managed memory with `MemoryManager`
- conflict handling before cloud sync
- encrypted local memory files
- cloud activation and ingest helpers

The private Django platform provides long-term cloud storage, API keys, device activations, owner isolation, dashboard operations, content library management, and the RAG/LLM integration boundary.

## How RAG Fits

ZHL LSTM Memory should use RAG as a recall layer on top of owner-scoped memory, not as a replacement for memory ownership and privacy controls.

Recommended flow:

1. The robot uses the SDK locally for short-term memory and candidate extraction.
2. Confirmed or important memories are synced to the cloud owner vault.
3. The platform retrieves only that owner's current facts and relevant memories.
4. The platform builds a prompt-ready memory context.
5. A chat LLM receives that memory context and answers the user.

The cloud platform version `0.2.6` exposes this boundary through:

```http
POST https://memory.zhlaistudio.com/api/v1/memories/rag-context/
Authorization: Bearer zhla_...
Content-Type: application/json

{
  "query": "favorite color and bedtime story preferences",
  "limit": 8,
  "include_facts": true
}
```

The response includes `rag_mode`, `facts`, `memories`, and `prompt_context`.

## LLM Boundary

The current public SDK does not call an LLM directly. This is intentional: different robots may use different cloud models, local private models, or future ZHL fine-tuned models.

The private platform now includes a disabled-by-default OpenAI-compatible provider adapter. Any model service that exposes `/v1/chat/completions` can be connected through the platform configuration.

Real LLM credentials must be stored in environment variables or a secret manager, not in robot code or Git.

## Model Status

The current Git delivery does not include proprietary LLM weights or a released fine-tuned model. The memory layer is model-agnostic and can later be paired with Qwen, Llama, DeepSeek, OpenAI-compatible services, local private models, or a future ZHL model.

Best current use cases:

- robot long-term memory
- local short-term robot memory
- personalized chat context
- child/family companion robots
- health and medication memory with privacy controls
- story, music, video, and education content personalization
