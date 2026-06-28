"""Load and normalise the project's OpenAPI schema.

By default the schema is generated *in-process* with drf-spectacular, so no
running HTTP server or self-call is required. A remote/file URL can be used
instead via ``DJANGO_OPENAPI_MCP["SCHEMA_URL"]``.
"""

from __future__ import annotations

from typing import Any

import httpx

from .conf import get_config


def get_schema() -> dict[str, Any]:
    """Return the OpenAPI 3 schema as a plain dict."""
    cfg = get_config()
    schema_url = cfg.get("SCHEMA_URL")
    if schema_url:
        return _fetch_schema(schema_url, cfg)
    return _generate_schema()


def _generate_schema() -> dict[str, Any]:
    """Generate the schema in-process using drf-spectacular."""
    from drf_spectacular.generators import SchemaGenerator

    generator = SchemaGenerator()
    schema = generator.get_schema(request=None, public=True)
    # get_schema returns an OrderedDict; callers only need mapping access.
    return dict(schema)


def _fetch_schema(url: str, cfg: dict[str, Any]) -> dict[str, Any]:
    resp = httpx.get(url, timeout=cfg["TIMEOUT"], follow_redirects=True)
    resp.raise_for_status()
    content_type = resp.headers.get("content-type", "")
    if "yaml" in content_type or url.endswith((".yaml", ".yml")):
        import yaml  # optional; only needed for YAML schemas

        return yaml.safe_load(resp.text)
    return resp.json()


def resolve_ref(schema: dict[str, Any], ref: str) -> dict[str, Any]:
    """Resolve a local ``$ref`` (e.g. ``#/components/schemas/Foo``)."""
    if not ref.startswith("#/"):
        raise ValueError(f"Only local refs are supported, got: {ref!r}")
    node: Any = schema
    for part in ref[2:].split("/"):
        node = node[part]
    return node
