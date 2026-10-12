"""Small, dependency-free signed session tokens for the API."""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import time


class InvalidSession(ValueError):
    pass


def _encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_session_token(user_id: int, session_nonce: str, secret: str, ttl_seconds: int) -> str:
    payload = {
        "sub": int(user_id),
        "sid": session_nonce,
        "exp": int(time.time()) + int(ttl_seconds),
        "v": 1,
    }
    encoded = _encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    signature = _encode(hmac.new(secret.encode(), encoded.encode(), hashlib.sha256).digest())
    return f"{encoded}.{signature}"


def verify_session_token(token: str, secret: str, now: int | None = None) -> tuple[int, str]:
    try:
        encoded, supplied_signature = token.split(".", 1)
        expected_signature = _encode(
            hmac.new(secret.encode(), encoded.encode(), hashlib.sha256).digest()
        )
        if not hmac.compare_digest(supplied_signature, expected_signature):
            raise InvalidSession("invalid signature")
        payload = json.loads(_decode(encoded))
        if (
            payload.get("v") != 1
            or not isinstance(payload.get("sub"), int)
            or not isinstance(payload.get("sid"), str)
            or not payload["sid"]
        ):
            raise InvalidSession("invalid payload")
        if int(payload.get("exp", 0)) <= (int(time.time()) if now is None else now):
            raise InvalidSession("expired")
        return payload["sub"], payload["sid"]
    except (
        ValueError,
        TypeError,
        KeyError,
        json.JSONDecodeError,
        UnicodeDecodeError,
        binascii.Error,
    ) as exc:
        if isinstance(exc, InvalidSession):
            raise
        raise InvalidSession("malformed token") from exc
