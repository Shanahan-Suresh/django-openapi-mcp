"""Credential passthrough for outgoing tool requests.

Real Django APIs are authenticated, so the generated tools must carry
credentials to the underlying endpoints. Credentials are static, read once from
configuration; forwarding an incoming caller's own auth (per-request
passthrough) is intentionally out of scope here.
"""

from __future__ import annotations

from typing import Any


def auth_headers(cfg: dict[str, Any]) -> dict[str, str]:
    """Build the auth headers to attach to every outgoing request."""
    auth = cfg.get("AUTH")
    if not auth:
        return {}

    kind = auth.get("type")
    if kind == "token":
        scheme = auth.get("scheme", "Token")
        return {"Authorization": f"{scheme} {auth['token']}"}
    if kind == "bearer":
        return {"Authorization": f"Bearer {auth['token']}"}
    if kind == "header":
        return {auth["name"]: auth["value"]}

    raise ValueError(f"Unknown AUTH type: {kind!r}")
