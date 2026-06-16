# 平台指南

当前 SDK 版本：`0.2.2`

`zhl-memory-core` 目前是纯 Python，不包含原生模型二进制、GPU kernel 或板卡专用编译扩展。因此现在 Ubuntu、Raspberry Pi 和 RK3588 都可以使用同一个 package tag。

目前不需要单独平台版本。只有当 SDK 未来加入原生加速、ONNX Runtime 变体、带编译依赖的本地向量索引或板卡 NPU 支持时，才需要平台专用构建。

## 推荐安装矩阵

| 平台 | 架构 | Package tag | 说明 |
| --- | --- | --- | --- |
| Ubuntu 22.04/24.04 | x86_64 或 arm64 | `v0.2.2` | 适合开发电脑和靠近云端的机器人应用。 |
| Raspberry Pi OS 64-bit | arm64 | `v0.2.2` | 建议使用 64-bit OS 和 Python 3.10+。本地 JSON state 放在持久化存储中。 |
| RK3588 Ubuntu/Debian | arm64 | `v0.2.2` | 当前纯 Python SDK 可直接运行。未来 NPU 加速应使用 platform extra 或专用 wheel。 |

## Ubuntu

```bash
python3 --version
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install git+https://github.com/ZHL-Technology/zhl-lstm-memory-sdk.git@v0.2.2
```

## Raspberry Pi

使用 Raspberry Pi OS 64-bit 和 Python 3.10 或更新版本。

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip git
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install git+https://github.com/ZHL-Technology/zhl-lstm-memory-sdk.git@v0.2.2
```

推荐本地 state 路径：

```python
from zhl_memory_core import MemoryManager

memory = MemoryManager(path="/var/lib/zhl-memory/robot-memory.json")
```

## RK3588

RK3588 Ubuntu 或 Debian arm64 现在也使用同一个安装方式：

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip git
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install git+https://github.com/ZHL-Technology/zhl-lstm-memory-sdk.git@v0.2.2
```

未来如果加入 RK3588 NPU 支持，不建议放进 base package。可以使用：

- `zhl-memory-core[rk3588]` optional dependencies
- `zhl_memory_core_rk3588` 专用 wheel
- 独立模型/runtime package，由机器人应用按设备加载

## 版本策略

只要 package 仍是纯 Python，所有平台使用同一个 project version。

如果未来需要原生平台构建，应保持 Python API 稳定，并从同一个 source tag 发布平台变体。
