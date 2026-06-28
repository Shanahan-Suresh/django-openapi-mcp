"""Configuration for django-openapi-mcp.

Reads ``settings.DJANGO_OPENAPI_MCP`` (a dict) and merges it over the defaults.

Example::

    DJANGO_OPENAPI_MCP = {
        "BASE_URL": "http://localhost:8000",
        "INCLUDE_METHODS": ["GET"],          # read-only by default
        "AUTH": {"type": "token", "token": "...", "scheme": "Token"},
    }
"""

from __future__ import annotations

from typing import Any

from django.conf import settings

DEFAULTS: dict[str, Any] = {
    # Where the generated tools send their HTTP requests (the live DRF API).
    "BASE_URL": "http://localhost:8000",
    # If set, fetch the OpenAPI schema from this URL instead of generating it
    # in-process with drf-spectacular. Useful for remote / non-DRF schemas.
    "SCHEMA_URL": None,
    # Server name advertised to MCP clients.
    "SERVER_NAME": "django-openapi-mcp",
    # SAFE BY DEFAULT: only read-only GET endpoints become tools. Add
    # "POST"/"PUT"/"PATCH"/"DELETE" to opt in to write operations.
    "INCLUDE_METHODS": ["GET"],
    # Optional allow/deny lists matched as path prefixes (e.g. "/api/v1/").
    "INCLUDE_PATHS": None,
    "EXCLUDE_PATHS": [],
    # Credential passthrough applied to every outgoing request. One of:
    #   {"type": "token",  "token": "...", "scheme": "Token"}   -> Authorization: Token ...
    #   {"type": "bearer", "token": "..."}                       -> Authorization: Bearer ...
    #   {"type": "header", "name": "X-API-Key", "value": "..."}  -> X-API-Key: ...
    "AUTH": None,
    # HTTP timeout (seconds) for schema fetch and tool execution.
    "TIMEOUT": 30,
}


def get_config() -> dict[str, Any]:
    """Return the effective configuration (defaults merged with user settings)."""
    user = getattr(settings, "DJANGO_OPENAPI_MCP", None) or {}
    return {**DEFAULTS, **user}
