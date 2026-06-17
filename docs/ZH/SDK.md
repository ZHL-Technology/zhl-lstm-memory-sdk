# ZHL Memory SDK Core 中文说明

当前 package 版本：`0.2.3`

可安装的 SDK 核心位于 `zhl_memory_core/`。它不依赖 Django，可以直接安装在机器人项目旁边。

```bash
pip install git+https://github.com/ZHL-Technology/zhl-lstm-memory-sdk.git
```

这个安装命令故意不固定 tag，因此开发设备默认会安装最新 SDK。只有生产机器人需要冻结 build 时，才建议指定 release tag。

## 激活流程

1. 为个人或公司创建 dashboard 用户。
2. 在 dashboard 左侧菜单打开 **API Keys**，创建一个命名清晰的 SDK API Key，并把 `allowed_devices` 设置为允许激活的机器人数量上限。
3. 从弹窗中复制生成的 `zhlsk_...` key。之后 owner 可以在同一个 dashboard 页面再次查看和复制完整 key。

服务端自动化也可以生成 SDK API Key：

```bash
.venv/bin/python manage.py issue_sdk_key \
  --username zhl-lstm \
  --name zhl-internal-robots \
  --account-type company \
  --company-name "ZHL Technology" \
  --allowed-devices 50
```

4. 机器人/设备激活一次：

```http
POST /api/v1/sdk/activate/
Content-Type: application/json

{
  "api_key": "zhlsk_...",
  "device_id": "robot-serial-001",
  "device_name": "Robot 001",
  "sdk_version": "0.2.3",
  "platform": "linux"
}
```

5. 响应会返回 `activation_token`。之后用它作为 bearer token：

```http
Authorization: Bearer zhla_...
```

## 本地 NER

只需要提取 facts 和 memory envelope 时，使用 `MemoryEngine`。

```python
from zhl_memory_core import MemoryEngine

engine = MemoryEngine()
envelope = engine.build_envelope("My name is Sara. I love blue rooms.")
payload = envelope.to_payload()
```

这个 payload 可以直接发送到 `/api/v1/memories/ingest/`。

## 本地托管记忆

机器人需要本地短期记忆、冲突检测和云端同步前的确认流程时，使用 `MemoryManager`。

```python
from zhl_memory_core import MemoryManager

memory = MemoryManager(path="./robot-memory.json")

memory.process("My name is Ady.")
conflict = memory.process("My name is Bob.")

print(conflict.pending_conflict)  # True
print(conflict.assistant)         # 询问替换旧值还是两个都保留

updated = memory.process("That was not real. Replace it with Bob.")
print(updated.memory_json)
```

生产机器人建议使用设备密钥或机器人安全存储中的 key material 加密本地 state 文件：

```python
from zhl_memory_core import MemoryManager

memory = MemoryManager(
    path="/var/lib/zhl-memory/short-term-memory.enc",
    encryption_key="load-this-from-the-robot-secure-store",
)
```

加密文件会以 `zhlmem1:` 开头，不会包含可直接读取的姓名、偏好、健康信息或记忆内容。如果打开加密文件时没有提供 `encryption_key`，SDK 会抛出明确错误，而不是重置 state。

## 冲突处理

`MemoryManager` 将以下字段视为单值身份信息：

- `first_name`
- `last_name`
- `age`
- `birth_date`

如果新值与当前值冲突，manager 会返回 `pending_conflict=True`，并且暂时不会保存新值。下一条用户消息会被当作解决冲突的确认：

- replace/update/correct：archive 旧值并保存新值
- keep both/two names/alias：两个值都保持 current
- cancel/ignore：不修改记忆

偏好、讨厌的内容、兴趣、药物和故事类记忆不是单值身份字段，默认可以保存多个条目。

## Dashboard Sandbox

Dashboard Sandbox 使用与 SDK manager 相同的记忆行为：

1. 用户像普通聊天一样输入。
2. 只有出现值得记住的内容时，memory engine 才提取候选 facts。
3. 右侧 Live memory JSON 只在 active memory 变化时更新。
4. 如果单值身份信息冲突，assistant 会询问是替换旧值还是两个都保留。
5. Sandbox 记忆只是临时测试状态，刷新 Sandbox 页面后会重置。

这让网页 sandbox 可以作为机器人团队在集成 SDK 前的测试界面。

## 平台说明

`zhl-memory-core` 在 Ubuntu、Raspberry Pi OS 和 RK3588 上保持同一个 Python API。本地加密存储使用 `cryptography` package。平台安装说明和未来构建策略见 [Platform Guide](PLATFORMS.md)。
