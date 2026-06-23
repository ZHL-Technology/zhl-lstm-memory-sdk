# RAG 与大模型集成说明

当前 SDK package 版本：`0.2.4`

## 范围说明

Public SDK 是机器人端的记忆核心。它不是已经训练好的大模型，也不是完整的传统文档型 RAG 系统。

SDK 提供：

- 使用 `MemoryEngine` 做本地记忆抽取
- 使用 `MemoryManager` 做本地短期托管记忆
- 云端同步前的冲突处理
- 加密本地记忆文件
- 云端 activation 和 ingest 辅助能力

Private Django 平台负责长期云端存储、API Key、设备激活、owner 隔离、dashboard 运维、内容库管理，以及 RAG/LLM 集成边界。

## RAG 如何接入

ZHL LSTM Memory 推荐把 RAG 作为 owner-scoped 记忆上方的召回层，而不是用 RAG 替代记忆 ownership 和隐私控制。

推荐流程：

1. 机器人使用 SDK 在本地做短期记忆和候选记忆抽取。
2. 已确认或重要的记忆同步到云端 owner vault。
3. 平台只从该 owner 的 current facts 和 relevant memories 中召回。
4. 平台构建 prompt-ready memory context。
5. 聊天大模型接收该 memory context 后回答用户。

云端平台 `0.2.8` 已经通过以下接口暴露这个边界：

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

响应包含 `rag_mode`、`facts`、`memories` 和 `prompt_context`。

## 大模型交付边界

当前已请求并交付的范围是短期记忆和长期记忆服务，不是聊天大模型。SDK 可以运行在贵司 STT 之后、贵司现有 LLM/对话系统之前，或作为贵司 LLM 输出后的记忆处理链路。

当前 public SDK 不直接调用大模型。它负责提取值得记住的信息、在对话期间管理本地短期状态，并把确认后的记忆同步到云端。贵司现有 LLM 仍然负责自然语言对话。

Private platform 已经加入默认关闭的 OpenAI-compatible provider adapter。这个 adapter 是贵司现有 LLM 或其他兼容模型服务的标准集成点，不代表当前交付 LLM。

下一阶段产品目标是把现有 OODI-X01 英文/中文 runtime 打包并稳定成完整机器人 AI
runtime SDK：Vosk ASR、Qwen-family 本地 LLM profiles，以及 high-level memory +
RAG + LLM orchestration。这不是要求从零开始重做一个新的 LLM。详见
[英文/中文完整机器人 AI Stack 交付约定](FULL_ROBOT_STACK.md)。波斯语不属于当前语言范围。

真实 LLM credential 必须放在环境变量或 secret manager 中，不能写入机器人代码或 Git。

## 模型状态

当前 Git 交付不包含自研大模型权重，也没有发布 fine-tuned 模型。记忆层是 model-agnostic，之后可以与 Qwen、Llama、DeepSeek、OpenAI-compatible 服务、本地私有模型或未来 ZHL 模型配合。

当前最适合场景：

- 机器人长期记忆
- 机器人本地短期记忆
- 个性化聊天上下文
- 儿童/家庭陪伴机器人
- 带隐私控制的健康和药物记忆
- 故事、音乐、视频和教育内容个性化
