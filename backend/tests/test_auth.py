import hashlib
import hmac
import json
from urllib.parse import urlencode

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.api.dependencies.auth import get_identity, validate_init_data
from app.config.settings import Settings

TOKEN = "123456:test-token-not-a-real-secret"


def signed_data(user_id=123, timestamp=1000, **extra):
    fields = {
        "auth_date": str(timestamp),
        "user": json.dumps({"id": user_id, "first_name": "Sardor"}, separators=(",", ":")),
        "query_id": "test",
        **extra,
    }
    secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
    check = "\n".join(f"{key}={value}" for key, value in sorted(fields.items()))
    fields["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


def test_valid_signature():
    result = validate_init_data(signed_data(), TOKEN, now=1001)
    assert result.id == 123
    assert result.first_name == "Sardor"


@pytest.mark.parametrize(
    "raw,token,now",
    [
        (signed_data().replace("Sardor", "Attacker"), TOKEN, 1001),
        (signed_data(), "wrong-token", 1001),
        (signed_data(), "", 1001),
        (signed_data(), TOKEN, 5000),
        (signed_data(timestamp=1100), TOKEN, 1000),
        (signed_data() + "&auth_date=1000", TOKEN, 1001),
        ("invalid", TOKEN, 1001),
        ("", TOKEN, 1001),
        (signed_data(user_id=True), TOKEN, 1001),
        (signed_data(user_id="123"), TOKEN, 1001),
        (signed_data(user_id=-1), TOKEN, 1001),
        (signed_data(user_id=2**64), TOKEN, 1001),
    ],
)
def test_reject_invalid_credentials(raw, token, now):
    with pytest.raises(HTTPException) as exc:
        validate_init_data(raw, token, now=now)
    assert exc.value.status_code == 401


def request(headers=(), host="127.0.0.1"):
    return Request({"type": "http", "headers": headers, "client": (host, 1234)})


def test_development_auth_requires_explicit_opt_in():
    settings = Settings(_env_file=None, dev_telegram_user_id=555)
    assert get_identity(request([(b"x-dev-auth", b"1")]), settings).id == 555
    for req in [
        request(),
        request([(b"x-dev-auth", b"1")], host="10.0.0.1"),
        request([(b"x-dev-auth", b"1"), (b"origin", b"https://evil.example")]),
        request([(b"x-dev-auth", b"1"), (b"authorization", b"tma bad")]),
    ]:
        with pytest.raises(HTTPException):
            get_identity(req, settings)


def test_development_auth_impossible_in_production():
    settings = Settings(
        _env_file=None,
        app_env="production",
        bot_token=TOKEN,
        cors_origins="https://app.example",
        dev_telegram_user_id=555,
    )
    with pytest.raises(HTTPException):
        get_identity(request([(b"x-dev-auth", b"1")]), settings)


def test_production_cors_must_be_explicit_and_https():
    for origins in ["*", "http://app.example"]:
        with pytest.raises(ValueError):
            Settings(_env_file=None, app_env="production", bot_token=TOKEN, cors_origins=origins)
