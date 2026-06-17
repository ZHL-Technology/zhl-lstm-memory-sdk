# Platform Guide

Current SDK version: `0.2.3`

`zhl-memory-core` currently keeps the same Python API across platforms and does not include native model binaries, GPU kernels, or board-specific compiled extensions. Local encrypted storage depends on the standard `cryptography` package. Because of that, the same public Git source works across Ubuntu, Raspberry Pi, and RK3588 today.

Separate platform builds are not required yet. Platform-specific packaging will become necessary if the SDK later includes native acceleration, ONNX Runtime variants, local vector indexes with compiled dependencies, or board-specific NPU support.

## Recommended Install Matrix

| Platform | Architecture | Install source | Notes |
| --- | --- | --- | --- |
| Ubuntu 22.04/24.04 | x86_64 or arm64 | latest public Git URL | Recommended for cloud-adjacent robot apps and developer laptops. |
| Raspberry Pi OS 64-bit | arm64 | latest public Git URL | Use a 64-bit OS and Python 3.10+. Keep local JSON state on persistent storage. |
| RK3588 Ubuntu/Debian | arm64 | latest public Git URL | Same SDK source works now. Future NPU acceleration should use a platform-specific extra or wheel. |

## Ubuntu

```bash
python3 --version
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install git+https://github.com/ZHL-Technology/zhl-lstm-memory-sdk.git
```

Smoke test:

```bash
.venv/bin/python - <<'PY'
from zhl_memory_core import MemoryManager, __version__

memory = MemoryManager()
memory.process("My name is Ady.")
conflict = memory.process("My name is Bob.")
print(__version__)
print(conflict.pending_conflict)
print(conflict.assistant)
PY
```

## Raspberry Pi

Use Raspberry Pi OS 64-bit with Python 3.10 or newer.

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip git
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install git+https://github.com/ZHL-Technology/zhl-lstm-memory-sdk.git
```

Recommended local state path:

```python
from zhl_memory_core import MemoryManager

memory = MemoryManager(path="/var/lib/zhl-memory/robot-memory.json")
```

For encrypted local state:

```python
memory = MemoryManager(
    path="/var/lib/zhl-memory/short-term-memory.enc",
    encryption_key="load-this-from-the-robot-secure-store",
)
```

## RK3588

For RK3588 boards running Ubuntu or Debian arm64, the current SDK installs the same way:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip git
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install git+https://github.com/ZHL-Technology/zhl-lstm-memory-sdk.git
```

Future RK3588 NPU support should not be mixed into the base package. Use one of these patterns later:

- `zhl-memory-core[rk3588]` for optional dependencies
- a board-specific wheel such as `zhl_memory_core_rk3588`
- a separate model/runtime package that the robot app loads only on RK3588

## Version Policy

Use the same project version for the Python SDK across all supported platforms while the package keeps one shared Python API.

When native platform builds become necessary, keep the Python API stable and publish platform variants from the same source tag.
