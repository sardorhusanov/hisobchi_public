"""Telegram initData is a short-lived bearer credential; never log it."""

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Annotated
from urllib.parse import parse_qsl

from fastapi import Depends, HTTPException, Request

from app.config.settings import Settings, get_settings


@dataclass(frozen=True)
class TelegramIdentity:
    id: int
    first_name: str


def validate_init_data(
    raw: str, token: str, max_age: int = 3600, now: int | None = None
) -> TelegramIdentity:
    try:
        if not token or not raw or len(raw) > 16384:
            raise ValueError
        pairs = parse_qsl(raw, keep_blank_values=True, strict_parsing=True, max_num_fields=32)
        fields = dict(pairs)
        if len(fields) != len(pairs):
            raise ValueError
        supplied = fields.pop("hash")
        if len(supplied) != 64:
            raise ValueError
        check = "\n".join(f"{key}={value}" for key, value in sorted(fields.items()))
        secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
        expected = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, supplied):
            raise ValueError
        auth_date = int(fields["auth_date"])
        timestamp = int(time.time()) if now is None else now
        if not timestamp - max_age <= auth_date <= timestamp + 30:
            raise ValueError
        user = json.loads(fields["user"])
        user_id = user["id"]
        name = user["first_name"]
        if (
            type(user_id) is not int
            or not 0 < user_id < 2**63
            or not isinstance(name, str)
            or not name.strip()
        ):
            raise ValueError
        return TelegramIdentity(user_id, name[:120])
    except (ValueError, KeyError, TypeError, OverflowError):
        raise HTTPException(
            401, "Telegram sessiyasi yaroqsiz yoki eskirgan. Ilovani qayta oching."
        ) from None


def get_identity(
    request: Request, settings: Annotated[Settings, Depends(get_settings)]
) -> TelegramIdentity:
    authorization = request.headers.get("Authorization", "")
    if authorization:
        scheme, _, credential = authorization.partition(" ")
        if scheme != "tma":
            raise HTTPException(401, "Telegram orqali kiring.")
        return validate_init_data(credential, settings.bot_token, settings.telegram_auth_max_age)
    # Explicit, loopback-only opt-in. No user ID is accepted from the client.
    if (
        settings.app_env == "development"
        and settings.dev_telegram_user_id
        and request.headers.get("X-Dev-Auth") == "1"
        and request.client
        and request.client.host in {"127.0.0.1", "::1", "localhost"}
    ):
        origin = request.headers.get("Origin")
        if origin and origin not in settings.allowed_origins:
            raise HTTPException(401, "Mahalliy kirishga ruxsat yo'q.")
        return TelegramIdentity(settings.dev_telegram_user_id, "Mahalliy foydalanuvchi")
    raise HTTPException(401, "Ilovani Telegram bot orqali oching.")
