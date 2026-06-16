# Versioning

Current SDK package version: `0.2.2`

ZHL LSTM Memory uses a semantic-style project version: `MAJOR.MINOR.PATCH`.

- `MAJOR`: incompatible SDK, cloud API, or memory-envelope changes.
- `MINOR`: backward-compatible SDK features, extraction rules, models, or cloud API routes.
- `PATCH`: bug fixes, documentation updates, migrations, and small safe improvements.

ZHL release numbers use carry-over at 10. For example:

- current: `0.2.2`
- next patch: `0.2.3`
- after `0.2.9`: `0.3.0`
- after `0.9.9`: `1.0.0`

Release changes must update:

- `VERSION`
- `pyproject.toml`
- `zhl_memory_core/__init__.py`
- `zhl_memory_core/client.py` default `sdk_version`
- `README.md`
- relevant files in `docs/`
- `CHANGELOG.md`
- Git tag, for example `v0.2.2`

While `zhl-memory-core` remains pure Python, Ubuntu, Raspberry Pi, and RK3588 use the same project version and package tag. If native platform builds are added later, they should be published from the same source tag and documented in [Platform Guide](PLATFORMS.md).
