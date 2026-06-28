"""Build a real MCP server from the generated tool specs.

Uses the official MCP SDK's low-level :class:`~mcp.server.lowlevel.Server`, which
lets us advertise tools with arbitrary per-endpoint JSON Schemas (``list_tools``)
and execute them against the live API (``call_tool``).
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import mcp.types as types
from mcp.server.lowlevel import Server

from .auth import auth_headers
from .conf import get_config
from .introspect import get_schema
from .tools import ToolSpec, build_tool_specs


def build_server() -> tuple[Server, list[ToolSpec]]:
    """Construct the MCP server and return it alongside the generated specs."""
    cfg = get_config()
    schema = get_schema()
    specs = build_tool_specs(schema)
    by_name = {spec.name: spec for spec in specs}

    server: Server = Server(cfg["SERVER_NAME"])

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name=spec.name,
                description=spec.description,
                inputSchema=spec.input_schema,
            )
            for spec in specs
        ]

    @server.call_tool()
    async def call_tool(
        name: str, arguments: dict[str, Any]
    ) -> list[types.TextContent]:
        spec = by_name.get(name)
        if spec is None:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
        text = await _execute(spec, arguments or {}, cfg)
        return [types.TextContent(type="text", text=text)]

    return server, specs


def _build_request(
    spec: ToolSpec, arguments: dict[str, Any], cfg: dict[str, Any]
) -> tuple[str, str, dict[str, Any], dict[str, str]]:
    """Map tool arguments onto an HTTP request: (method, url, query, headers).

    Path parameters are substituted into the URL template; query parameters are
    collected separately. Pure and side-effect free, so it can be unit-tested
    without a live API.
    """
    path = spec.path
    query: dict[str, Any] = {}
    path_params = {p["name"] for p in spec.params if p["in"] == "path"}
    query_params = {p["name"] for p in spec.params if p["in"] == "query"}

    for key, value in arguments.items():
        if key in path_params:
            path = path.replace("{" + key + "}", str(value))
        elif key in query_params:
            query[key] = value

    url = cfg["BASE_URL"].rstrip("/") + path
    headers = {"Accept": "application/json", **auth_headers(cfg)}
    return spec.method, url, query, headers


def _format_response(resp: httpx.Response, method: str, url: str) -> str:
    """Render an HTTP response as readable text, pretty-printing JSON bodies."""
    try:
        body = json.dumps(resp.json(), indent=2)
    except ValueError:
        body = resp.text
    return f"HTTP {resp.status_code} {method} {url}\n\n{body}"


async def _execute(
    spec: ToolSpec, arguments: dict[str, Any], cfg: dict[str, Any]
) -> str:
    """Execute a tool call against the live API and return a text result."""
    method, url, query, headers = _build_request(spec, arguments, cfg)

    try:
        async with httpx.AsyncClient(timeout=cfg["TIMEOUT"]) as client:
            resp = await client.request(
                method, url, params=query, headers=headers, follow_redirects=True
            )
    except httpx.HTTPError as exc:
        return f"Request to {url} failed: {exc}"

    return _format_response(resp, method, url)
