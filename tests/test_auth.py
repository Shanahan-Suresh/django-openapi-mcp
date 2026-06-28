"""Unit tests for django_openapi_mcp.auth.auth_headers."""

import pytest

from django_openapi_mcp.auth import auth_headers


def test_no_auth_returns_empty():
    assert auth_headers({}) == {}
    assert auth_headers({"AUTH": None}) == {}


def test_token_auth_uses_default_scheme():
    headers = auth_headers({"AUTH": {"type": "token", "token": "abc"}})
    assert headers == {"Authorization": "Token abc"}


def test_token_auth_honours_custom_scheme():
    headers = auth_headers(
        {"AUTH": {"type": "token", "token": "abc", "scheme": "Api-Key"}}
    )
    assert headers == {"Authorization": "Api-Key abc"}


def test_bearer_auth():
    headers = auth_headers({"AUTH": {"type": "bearer", "token": "xyz"}})
    assert headers == {"Authorization": "Bearer xyz"}


def test_custom_header_auth():
    headers = auth_headers(
        {"AUTH": {"type": "header", "name": "X-API-Key", "value": "secret"}}
    )
    assert headers == {"X-API-Key": "secret"}


def test_unknown_auth_type_raises():
    with pytest.raises(ValueError, match="Unknown AUTH type"):
        auth_headers({"AUTH": {"type": "magic"}})
