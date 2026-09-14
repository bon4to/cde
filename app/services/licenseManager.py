"""
License file reader for paid CDE modules.

The app only reads/decrypts license files. Files are expected to be produced by
an external generator using the same token format.
"""

import base64
import hashlib
import hmac
import json
import os
from typing import Any


LICENSE_FILE_ENV = "CDE_LICENSE_FILE"
LICENSE_SECRET_ENV = "CDE_LICENSE_SECRET"
DEFAULT_PAID_MODULES = {"MOV008", "PRC010", "ENV006"}


def _base64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _base64_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _keystream(secret: bytes, nonce: bytes, size: int) -> bytes:
    stream = bytearray()
    counter = 0

    while len(stream) < size:
        block = hmac.new(
            secret,
            nonce + counter.to_bytes(4, "big"),
            hashlib.sha256,
        ).digest()
        stream.extend(block)
        counter += 1

    return bytes(stream[:size])


def _normalize_modules(data: dict[str, Any]) -> set[str]:
    modules = data.get("modules", data.get("allowed_modules", []))
    if not isinstance(modules, list):
        return set()
    return {str(module).strip().upper() for module in modules if str(module).strip()}


def encrypt_license_payload(payload: dict[str, Any], secret: str) -> str:
    """
    Encode a license payload.

    This helper is intentionally file/route agnostic so the external generator
    can reuse the format without coupling to Flask.
    """
    if not secret:
        raise ValueError("license secret is required")

    secret_bytes = secret.encode("utf-8")
    nonce = os.urandom(16)
    plain = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    stream = _keystream(secret_bytes, nonce, len(plain))
    cipher = bytes(value ^ stream[index] for index, value in enumerate(plain))
    signature = hmac.new(secret_bytes, nonce + cipher, hashlib.sha256).hexdigest()

    return json.dumps(
        {
            "version": 1,
            "nonce": _base64_encode(nonce),
            "payload": _base64_encode(cipher),
            "signature": signature,
        },
        separators=(",", ":"),
    )


def decrypt_license_token(token: str, secret: str | None = None) -> dict[str, Any]:
    secret = secret or os.getenv(LICENSE_SECRET_ENV, "")
    if not token or not secret:
        return {}

    try:
        envelope = json.loads(token)
        nonce = _base64_decode(envelope["nonce"])
        cipher = _base64_decode(envelope["payload"])
        signature = envelope["signature"]
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return {}

    secret_bytes = secret.encode("utf-8")
    expected = hmac.new(secret_bytes, nonce + cipher, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(str(signature), expected):
        return {}

    stream = _keystream(secret_bytes, nonce, len(cipher))
    plain = bytes(value ^ stream[index] for index, value in enumerate(cipher))

    try:
        data = json.loads(plain.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}

    return data if isinstance(data, dict) else {}


def load_license() -> dict[str, Any]:
    path = os.getenv(LICENSE_FILE_ENV, "")
    if not path:
        return {}

    try:
        with open(path, "r", encoding="utf-8") as license_file:
            return decrypt_license_token(license_file.read().strip())
    except OSError:
        return {}


def allowed_modules() -> set[str]:
    return _normalize_modules(load_license())


def is_module_allowed(module_id: str) -> bool:
    return str(module_id).strip().upper() in allowed_modules()
