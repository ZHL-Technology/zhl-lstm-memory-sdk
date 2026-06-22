# 版本策略

当前 SDK package 版本：`0.2.4`

ZHL LSTM Memory 使用 semantic-style 项目版本：`MAJOR.MINOR.PATCH`。

- `MAJOR`：不兼容的 SDK、cloud API 或 memory-envelope 变更。
- `MINOR`：向后兼容的 SDK 功能、extraction rule、model 或 cloud API route。
- `PATCH`：bug fix、文档更新、migration 和小型安全改进。

ZHL 版本号在到达 10 时进位。例如：

- 当前：`0.2.4`
- 下一个 patch：`0.2.5`
- `0.2.9` 之后：`0.3.0`
- `0.9.9` 之后：`1.0.0`

每次发布需要更新：

- `VERSION`
- `pyproject.toml`
- `zhl_memory_core/__init__.py`
- `zhl_memory_core/client.py` 默认 `sdk_version`
- `README.md`
- `docs/` 中相关文档
- `CHANGELOG.md`
- Git tag，例如 `v0.2.4`

只要 `zhl-memory-core` 在各平台保持同一个 Python API，Ubuntu、Raspberry Pi 和 RK3588 使用同一个 project version 和 Git source。未来如果加入原生平台构建，应从同一个 source tag 发布，并在 [Platform Guide](PLATFORMS.md) 中说明。
