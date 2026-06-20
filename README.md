# ZHL LSTM Memory SDK

Standalone Python SDK for ZHL robot memory extraction, local managed memory, conflict handling, and cloud memory API integration.

Current package version: `0.2.3`

Repository: `https://github.com/ZHL-Technology/zhl-lstm-memory-sdk`

## Documentation

Choose your language:

- [English Documentation](docs/EN/SDK.md)
- [中文文档](docs/ZH/SDK.md)
- [RAG And LLM Integration Notes](docs/EN/RAG_LLM.md)
- [RAG 与大模型集成说明](docs/ZH/RAG_LLM.md)

## Quick Install

Public HTTPS install:

```bash
pip install git+https://github.com/ZHL-Technology/zhl-lstm-memory-sdk.git
```

This command intentionally omits a release tag so it installs the latest public SDK.

SSH install for ZHL developers:

```bash
pip install git+ssh://git@github.com/ZHL-Technology/zhl-lstm-memory-sdk.git
```

## Quick Usage

```python
from zhl_memory_core import MemoryManager

memory = MemoryManager(
    path="./robot-memory.enc",
    encryption_key="load-this-from-the-robot-secure-store",
)
result = memory.process("My name is Sara. My favorite color is blue.")

print(result.memory_json)
```
