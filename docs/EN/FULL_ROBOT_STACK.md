# Full English/Chinese Robot AI Stack Contract

Current SDK package version: `0.2.4`

This document defines the target package shape for the next delivery phase.
The current public repository is a memory SDK. The required product is a
downloadable robot AI runtime SDK that keeps voice recognition, local LLM,
memory, and cloud platform sync aligned.

## Language Scope

Supported conversation languages for this phase:

- English
- Chinese

Persian is intentionally out of scope for this phase. Do not add Persian ASR,
LLM prompts, test data, or model requirements until a later product decision
adds Persian as an official language.

## Required Developer Experience

A developer should be able to clone or install the repository, provide platform
credentials, run one bootstrap command, and get a complete local robot runtime
stack:

```text
English/Chinese Vosk ASR
English/Chinese local chat LLM
local short-term memory
encrypted memory state
cloud activation and memory sync
owner-scoped platform RAG context
health checks and smoke tests
```

The package should not require developers to manually discover model URLs,
wire local services together by hand, or guess environment variables.

## Important Packaging Rule

Do not commit large model binaries to Git.

The repository should include:

- model manifest files
- pinned model URLs
- expected filenames
- checksums when available
- license notes
- installer/downloader CLI
- runtime config templates
- health checks

The installer should download models into an ignored local asset directory such
as:

```text
~/.cache/zhl-memory-sdk/models/
~/.local/share/zhl-memory-sdk/models/
./assets/models/               # for developer demos only, ignored by Git
```

This keeps the repository small while still giving developers a complete
one-command setup.

## Target Runtime Architecture

```text
microphone/audio input
  -> Vosk ASR (English/Chinese)
  -> language detection / command router
  -> local MemoryManager extraction and conflict handling
  -> optional cloud ingest for confirmed memory
  -> platform RAG context retrieval
  -> local English/Chinese LLM
  -> response text
  -> robot app TTS / animation / motion layer
```

The SDK should not own robot motion or robot-specific hardware drivers. Those
belong in the robot application. The SDK should own the voice-memory-LLM
integration boundary.

## Required Components

### 1. Vosk ASR Bundle

Provide an optional ASR package or module with:

```text
English Vosk model manifest
Chinese Vosk model manifest
download/install command
model path resolver
basic transcription smoke test
```

Recommended command shape:

```bash
zhl-memory assets install-asr --languages en,zh
zhl-memory doctor asr
zhl-memory transcribe --language en sample.wav
zhl-memory transcribe --language zh sample.wav
```

### 2. Local English/Chinese LLM Bundle

Provide a local LLM adapter with a default English/Chinese model profile.

The current OODI robot uses Qwen-family local chat models because native Chinese
quality is required. The SDK should make that a first-class profile, for
example:

```text
qwen2.5-0.5b-instruct-q4_k_m.gguf  # fast/small profile
qwen2.5-1.5b-instruct-q4_k_m.gguf  # balanced profile
```

The package should support a local OpenAI-compatible endpoint, such as
`llama-server`, and should also allow a compatible remote/private endpoint.

Recommended command shape:

```bash
zhl-memory assets install-llm --profile balanced
zhl-memory llm start
zhl-memory doctor llm
zhl-memory chat "How are you?"
zhl-memory chat "你好，你好吗？"
```

LLM language policy:

- If the user speaks English, answer in English.
- If the user speaks Chinese, answer in natural Chinese.
- Do not answer in Chinese to English unless the user asks for Chinese.
- Do not answer in English to Chinese unless the user asks for English.

### 3. Memory Core

Keep the existing memory responsibilities:

```text
MemoryEngine
MemoryManager
encrypted local memory state
conflict handling
current facts
memory JSON
```

Memory must run before the LLM prompt is built so personalization can be added
to the prompt context.

### 4. Platform Connection

Keep the existing platform connection:

```text
SDK API key activation
activation token persistence
cloud ingest
secret redaction
User-Agent for headless robots
HTTP timeout override
```

Add a high-level helper that combines local memory and cloud sync so robot apps
do not have to reimplement the same bridge repeatedly.

Recommended class shape:

```python
from zhl_memory_core import RobotMemoryBridge

bridge = RobotMemoryBridge.from_env()
turn = bridge.process_user_text("My favorite color is blue.", language="en")
messages = bridge.build_llm_messages(user_text="Tell me a story.", language="en")
```

### 5. RAG Context

The package should expose a client helper for:

```text
POST /api/v1/memories/rag-context/
```

The helper should return:

```text
facts
memories
prompt_context
```

The local LLM adapter should accept this `prompt_context` directly.

### 6. Unified CLI

The package should expose one CLI entry point:

```bash
zhl-memory
```

Required commands:

```text
zhl-memory bootstrap
zhl-memory assets install-asr --languages en,zh
zhl-memory assets install-llm --profile balanced
zhl-memory doctor
zhl-memory activate
zhl-memory memory-smoke
zhl-memory rag-smoke
zhl-memory llm start
zhl-memory chat "Hello"
zhl-memory chat "你好"
```

### 7. Environment Contract

Minimum environment variables:

```text
ZHL_MEMORY_BASE_URL=https://memory.zhlaistudio.com
ZHL_MEMORY_API_KEY=<real SDK key, never committed>
ZHL_MEMORY_DEVICE_ID=<stable robot/developer device id>
ZHL_MEMORY_DEVICE_NAME=<human-readable name>
ZHL_MEMORY_ACTIVATION_TOKEN_PATH=~/.local/share/zhl-memory-sdk/activation-token.txt
ZHL_MEMORY_STATE_PATH=~/.local/share/zhl-memory-sdk/short-term-memory.enc
ZHL_MEMORY_KEY_PATH=~/.local/share/zhl-memory-sdk/local.key
ZHL_MEMORY_CLOUD_SYNC=1
ZHL_MEMORY_USER_AGENT=zhl-memory-core/0.3.0
ZHL_MEMORY_HTTP_TIMEOUT_S=12
ZHL_ASR_LANGUAGES=en,zh
ZHL_LLM_LANGUAGE_SCOPE=en,zh
ZHL_LLM_PROFILE=balanced
ZHL_LLM_LOCAL_URL=http://127.0.0.1:8080
```

Do not use Persian language defaults in this phase.

## Suggested Package Layout

```text
zhl_memory_core/
  client.py
  engine.py
  manager.py
  robot_bridge.py
  rag.py
  cli.py
  assets.py
  llm.py
  asr.py
  manifests/
    asr_vosk_en.json
    asr_vosk_zh.json
    llm_qwen_en_zh.json
tests/
  test_memory_core.py
  test_robot_bridge.py
  test_rag_client.py
  test_asset_manifest.py
  test_llm_language_policy.py
docs/
  EN/FULL_ROBOT_STACK.md
  ZH/FULL_ROBOT_STACK.md
```

## Acceptance Criteria

The next full-stack SDK phase is complete when:

1. A developer can install the repository and run `zhl-memory bootstrap`.

2. Bootstrap downloads or verifies English/Chinese Vosk assets and the selected
   English/Chinese LLM profile.

3. `zhl-memory doctor` confirms ASR, LLM, local memory, and platform connection.

4. `zhl-memory memory-smoke` activates with the platform and syncs a harmless
   memory test without printing secrets.

5. `zhl-memory chat "How are you?"` answers in English.

6. `zhl-memory chat "你好，你好吗？"` answers in Chinese.

7. Memory facts can be injected into the LLM prompt without the developer
   writing custom glue code.

8. Cloud sync failures do not break local chat.

9. API keys and activation tokens never appear in logs, exceptions, docs, tests,
   or Git.

10. The package contains no Persian language assumptions.

## Current Gap In Version 0.2.4

Version `0.2.4` has the memory and platform foundation, including the headless
robot User-Agent fix. It does not yet include:

```text
Vosk installer/runtime
local LLM installer/runtime
Qwen profile management
unified robot stack CLI
high-level Memory + RAG + LLM orchestration helper
```

Those items should be implemented before calling the repository a complete
robot AI runtime SDK.

