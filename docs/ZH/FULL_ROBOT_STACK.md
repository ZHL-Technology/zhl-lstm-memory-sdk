# 英文/中文完整机器人 AI Stack 交付约定

当前 SDK package 版本：`0.2.4`

本文定义下一阶段的目标 package 形态。当前 public repository 是记忆 SDK。
下一阶段需要交付的是可下载、可 bootstrap 的机器人 AI runtime SDK，把现有
OODI-X01 英文/中文 runtime 工作打包并稳定下来：语音识别、本地大模型、记忆和
云端平台同步。

这不是要求从零开始训练或重做一个新的 LLM。参考实现已经在 OODI-X01 robot
repository 中存在，下一步应该是 extraction、cleanup、testing 和 packaging。

## 语言范围

本阶段正式支持的对话语言：

- English
- 中文

波斯语不在本阶段范围内。在后续产品决策正式加入波斯语之前，不要加入波斯语
ASR、LLM prompt、测试数据或模型需求。

## 开发者体验目标

开发者应该可以 clone 或 install repository，提供平台 credential，运行一个
bootstrap 命令，然后得到完整本地机器人 runtime stack：

```text
英文/中文 Vosk ASR
英文/中文本地聊天大模型
本地短期记忆
加密记忆状态
云端 activation 和 memory sync
owner-scoped 平台 RAG context
health checks 和 smoke tests
```

package 不应该要求开发者手动查找模型 URL、自己拼接本地服务、或猜测环境变量。

## 重要打包规则

不要把大型模型二进制文件 commit 到 Git。

repository 应包含：

- model manifest files
- pinned model URLs
- expected filenames
- checksums when available
- license notes
- installer/downloader CLI
- runtime config templates
- health checks

installer 应把模型下载到被 Git 忽略的本地 asset 目录，例如：

```text
~/.cache/zhl-memory-sdk/models/
~/.local/share/zhl-memory-sdk/models/
./assets/models/               # only for developer demos, ignored by Git
```

这样 repository 保持轻量，同时仍然给开发者完整的一键 setup 体验。

## 目标 Runtime 架构

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

SDK 不应负责机器人运动或硬件 driver。这些属于 robot application。SDK 应负责
voice-memory-LLM integration boundary。

## 必需组件

### 1. Vosk ASR Bundle

提供可选 ASR package/module：

```text
English Vosk model manifest
Chinese Vosk model manifest
download/install command
model path resolver
basic transcription smoke test
```

建议命令：

```bash
zhl-memory assets install-asr --languages en,zh
zhl-memory doctor asr
zhl-memory transcribe --language en sample.wav
zhl-memory transcribe --language zh sample.wav
```

### 2. 本地英文/中文 LLM Bundle

提供 local LLM adapter，并提供默认英文/中文模型 profile。

当前 OODI robot 使用 Qwen-family 本地聊天模型，因为必须有 native Chinese 质量。
SDK 应把它作为 first-class profile，例如：

```text
qwen2.5-0.5b-instruct-q4_k_m.gguf  # fast/small profile
qwen2.5-1.5b-instruct-q4_k_m.gguf  # balanced profile
```

package 应支持本地 OpenAI-compatible endpoint，例如 `llama-server`，也应允许兼容的
remote/private endpoint。

需要保留的 OODI-X01 参考行为：

```text
llama-server OpenAI-compatible local endpoint
Qwen2.5 GGUF model profiles: fast/small/balanced/quality
strict English-in-English and Chinese-in-Chinese reply policy
short child-safe answers
memory context inserted as additional runtime system context
cloud sync runs outside the critical chat latency path
```

来自 OODI-X01 的已知稳定性工作：

```text
Vosk English 和 Chinese recognizers 会同时运行。
Chinese recognizer 可能从 English audio hallucinate 短中文片段。
arbitration layer 必须拒绝低置信度 cross-language transcripts。
LLM prompt/postprocess 必须拒绝 language mixing，而不是用错误语言说话。
```

建议命令：

```bash
zhl-memory assets install-llm --profile balanced
zhl-memory llm start
zhl-memory doctor llm
zhl-memory chat "How are you?"
zhl-memory chat "你好，你好吗？"
```

LLM 语言策略：

- 用户说英文时，用英文回答。
- 用户说中文时，用自然中文回答。
- 除非用户要求中文，否则不要用中文回答英文输入。
- 除非用户要求英文，否则不要用英文回答中文输入。

### 3. Memory Core

保留现有记忆职责：

```text
MemoryEngine
MemoryManager
encrypted local memory state
conflict handling
current facts
memory JSON
```

Memory 必须在构建 LLM prompt 之前运行，这样 personalization 可以进入 prompt context。

### 4. 平台连接

保留现有平台连接能力：

```text
SDK API key activation
activation token persistence
cloud ingest
secret redaction
User-Agent for headless robots
HTTP timeout override
```

增加一个 high-level helper，把 local memory 和 cloud sync 合在一起，避免 robot app
重复实现 bridge。

建议 class：

```python
from zhl_memory_core import RobotMemoryBridge

bridge = RobotMemoryBridge.from_env()
turn = bridge.process_user_text("My favorite color is blue.", language="en")
messages = bridge.build_llm_messages(user_text="Tell me a story.", language="en")
```

### 5. RAG Context

package 应提供 client helper：

```text
POST /api/v1/memories/rag-context/
```

helper 应返回：

```text
facts
memories
prompt_context
```

local LLM adapter 应可以直接接收这个 `prompt_context`。

### 6. 统一 CLI

package 应暴露一个 CLI entry point：

```bash
zhl-memory
```

必需命令：

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

### 7. 环境变量约定

最小环境变量：

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

本阶段不要使用波斯语默认值。

## 建议 Package Layout

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

## 验收标准

下一阶段 full-stack SDK 完成条件：

1. 开发者可以 install repository 并运行 `zhl-memory bootstrap`。

2. bootstrap 下载或验证英文/中文 Vosk assets 和选定英文/中文 LLM profile。

3. `zhl-memory doctor` 确认 ASR、LLM、本地记忆和平台连接。

4. `zhl-memory memory-smoke` 可以 activation 到平台并同步无害测试记忆，同时不打印
   secret。

5. `zhl-memory chat "How are you?"` 用英文回答。

6. `zhl-memory chat "你好，你好吗？"` 用中文回答。

7. memory facts 可以进入 LLM prompt，开发者不需要写自定义 glue code。

8. cloud sync 失败时，本地 chat 不应中断。

9. API key 和 activation token 不应出现在 logs、exceptions、docs、tests 或 Git。

10. package 不包含波斯语假设。

## Version 0.2.4 当前缺口

Version `0.2.4` 已具备 memory 和 platform foundation，包括 headless robot
User-Agent fix。它还没有包含：

```text
Vosk installer/runtime
local LLM installer/runtime
Qwen profile management
unified robot stack CLI
high-level Memory + RAG + LLM orchestration helper
```

在这些内容完成之前，不能把 repository 称为完整 robot AI runtime SDK。
