# ZHL LSTM Memory SDK

Standalone Python SDK for ZHL robot memory extraction, local managed memory, conflict handling, and cloud memory API integration.

Current package version: `0.2.2`

Repository: `https://github.com/ZHL-Technology/zhl-lstm-memory-sdk`

## Documentation

Choose your language:

- [English Documentation](docs/EN/README.md)
- [中文文档](docs/ZH/README.md)

## Quick Install

Public HTTPS install:

```bash
pip install git+https://github.com/ZHL-Technology/zhl-lstm-memory-sdk.git@v0.2.2
```

SSH install for ZHL developers:

```bash
pip install git+ssh://git@github.com/ZHL-Technology/zhl-lstm-memory-sdk.git@v0.2.2
```

## Quick Usage

```python
from zhl_memory_core import MemoryManager

memory = MemoryManager(path="./robot-memory.json")
result = memory.process("My name is Sara. My favorite color is blue.")

print(result.memory_json)
```
