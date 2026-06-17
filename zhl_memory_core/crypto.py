import base64
import hashlib
import json

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:  # pragma: no cover - exercised only when optional dependency is absent.
    Fernet = None
    InvalidToken = Exception


ENCRYPTED_STATE_PREFIX = "zhlmem1:"


def _require_fernet():
    if Fernet is None:
        raise RuntimeError("Encrypted memory storage requires the cryptography package.")


def _fernet(encryption_key):
    _require_fernet()
    material = str(encryption_key).encode("utf-8")
    key = base64.urlsafe_b64encode(hashlib.sha256(material).digest())
    return Fernet(key)


def dump_state(state, encryption_key=None):
    payload = json.dumps(state, ensure_ascii=False, indent=2)
    if not encryption_key:
        return payload
    encrypted = _fernet(encryption_key).encrypt(payload.encode("utf-8")).decode("utf-8")
    return f"{ENCRYPTED_STATE_PREFIX}{encrypted}"


def load_state(raw_payload, encryption_key=None):
    if raw_payload.startswith(ENCRYPTED_STATE_PREFIX):
        if not encryption_key:
            raise RuntimeError("Encrypted memory state requires encryption_key.")
        encrypted = raw_payload[len(ENCRYPTED_STATE_PREFIX) :]
        try:
            raw_payload = _fernet(encryption_key).decrypt(encrypted.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise RuntimeError("Invalid encryption_key for local memory state.") from exc
    return json.loads(raw_payload)
