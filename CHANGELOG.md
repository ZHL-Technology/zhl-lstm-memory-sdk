# Changelog

## 0.2.4 - 2026-06-22

- Added a default SDK User-Agent for headless robot API calls.
- Added `ZHL_MEMORY_USER_AGENT` and `ZHL_MEMORY_HTTP_TIMEOUT_S` overrides.
- Reduced default SDK HTTP timeout for robot runtimes.
- Redacted SDK API keys and activation tokens from HTTP error messages.

## 0.2.3 - 2026-06-17

- Added encrypted local memory state support for `MemoryManager`.
- Added `cryptography` as the SDK storage encryption dependency.
- Documented robot-side short-term memory encryption.

## 0.2.2 - 2026-06-16

- Published the standalone SDK in the public `zhl-lstm-memory-sdk` repository.
- Added separate English and Chinese documentation folders.
- Added pure-Python SDK tests and CI.

## 0.2.1 - 2026-06-16

- Fixed English NER so casual state phrases such as "I am tired" are not stored as first names.
- Added regression tests for the tired-as-name false positive.

## 0.2.0 - 2026-06-16

- Added package-level `MemoryManager` for local managed memory.
- Added conflict detection for single-value identity facts such as name, age, and birth date.
- Added replace-vs-keep-both resolution flow for conflicting memory facts.
- Archived replaced local memories while keeping audit history out of active memory JSON.
- Documented SDK managed memory usage.
