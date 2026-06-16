# ZHL Memory SDK Core

Current package version: `0.2.2`

The package-ready core lives in `zhl_memory_core/`. It has no Django dependency and can be installed beside robot code without pulling in the Django dashboard.

```bash
pip install git+https://github.com/ZHL-Technology/zhl-lstm-memory-sdk.git@v0.2.2
```

## Activation Flow

1. Create a dashboard user for a person or company.
2. Open **API Keys** in the dashboard and create a named SDK API key. Set `allowed_devices` to the maximum number of robots that can activate with that key.
3. Copy the generated `zhlsk_...` key from the modal. The owner can view and copy the full key again later from the same dashboard page.

Server-side automation can also issue an SDK API key:

```bash
.venv/bin/python manage.py issue_sdk_key \
  --username zhl-lstm \
  --name zhl-internal-robots \
  --account-type company \
  --company-name "ZHL Technology" \
  --allowed-devices 50
```

4. A robot/device activates once:

```http
POST /api/v1/sdk/activate/
Content-Type: application/json

{
  "api_key": "zhlsk_...",
  "device_id": "robot-serial-001",
  "device_name": "Robot 001",
  "sdk_version": "0.2.2",
  "platform": "linux"
}
```

5. The response returns an `activation_token`. Use it as bearer token:

```http
Authorization: Bearer zhla_...
```

## Local NER

```python
from zhl_memory_core import MemoryEngine

engine = MemoryEngine()
envelope = engine.build_envelope("My name is Sara. I love blue rooms.")
payload = envelope.to_payload()
```

The payload is compatible with `/api/v1/memories/ingest/`.

## Local Managed Memory

Use `MemoryManager` when the robot needs local short-term memory with conflict handling before syncing to cloud.

```python
from zhl_memory_core import MemoryManager

memory = MemoryManager(path="./robot-memory.json")

result = memory.process("My name is Ady.")
print(result.memory_json)

conflict = memory.process("My name is Bob.")
print(conflict.pending_conflict)  # True
print(conflict.assistant)         # asks whether to replace the old value or keep both

updated = memory.process("That was not real. Replace it with Bob.")
print(updated.memory_json)
```

Single-value identity facts such as `first_name`, `last_name`, `age`, and `birth_date` are not silently duplicated when a different value appears later. The manager asks for confirmation first. If the user says they have two names or wants to keep both, both values stay current. If the user confirms replacement, the old memory is archived and removed from the active memory JSON.

### Conflict Behavior

`MemoryManager` treats these keys as single-value identity facts:

- `first_name`
- `last_name`
- `age`
- `birth_date`

When a new value conflicts with a current value, the manager returns `pending_conflict=True` and does not save the new value yet. The next user message is treated as a resolution:

- replace/update/correct: archive old value and save the new one
- keep both/two names/alias: keep both values current
- cancel/ignore: leave memory unchanged

Preferences, dislikes, interests, medications, and stories are not handled as single-value identity facts. They can store multiple entries unless the robot application adds stricter business rules.

## Dashboard Sandbox

The dashboard Sandbox uses the same memory behavior as the SDK manager:

1. User chats normally.
2. The memory engine extracts candidate facts only when the text contains memory-worthy details.
3. The right-side Live memory JSON updates only when active memory changes.
4. If a single-value identity fact conflicts, the assistant asks whether to replace the old value or keep both.
5. Sandbox memory is temporary test state and resets when the Sandbox page is refreshed.

This makes the web sandbox a practical test surface for robot teams before they install the SDK in robot code.

## Platform Notes

`zhl-memory-core` `0.2.2` is pure Python. Ubuntu, Raspberry Pi OS, and RK3588 boards can use the same package tag today. See [Platform Guide](PLATFORMS.md) for platform-specific install notes and future build policy.

## Cloud Analyze

```http
POST /api/v1/memories/analyze/
Authorization: Bearer zhla_...
Content-Type: application/json

{"conversation_text": "My birthday is May 12. I take aspirin."}
```
