"""Turn OpenAPI operations into MCP tool specifications.

Each operation becomes a :class:`ToolSpec`: a name, a description, a JSON-Schema
describing its inputs (path + query parameters), and enough routing info to
execute the call later. Which HTTP methods become tools is controlled by
``INCLUDE_METHODS`` (read-only ``GET`` by default); request bodies for write
operations are intentionally out of scope.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .conf import get_config
from .introspect import resolve_ref

_NAME_RE = re.compile(r"[^a-zA-Z0-9_-]")


@dataclass
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]
    method: str
    path: str
    params: list[dict[str, str]] = field(default_factory=list)  # [{"name", "in"}]


def build_tool_specs(schema: dict[str, Any]) -> list[ToolSpec]:
    """Build the list of tool specs from an OpenAPI schema dict."""
    cfg = get_config()
    include_methods = {m.upper() for m in cfg["INCLUDE_METHODS"]}
    specs: list[ToolSpec] = []
    seen: set[str] = set()

    for path, path_item in (schema.get("paths") or {}).items():
        if not isinstance(path_item, dict) or _is_excluded(path, cfg):
            continue
        for method, operation in path_item.items():
            if method.upper() not in include_methods or not isinstance(operation, dict):
                continue
            spec = _build_one(schema, path, method.upper(), operation)
            spec.name = _dedupe_name(spec.name, seen)
            seen.add(spec.name)
            specs.append(spec)
    return specs


def _dedupe_name(name: str, seen: set[str]) -> str:
    """Return ``name`` (or a suffixed variant) that does not collide with ``seen``.

    Duplicate ``operationId``s would otherwise produce colliding tool names,
    which MCP clients reject.
    """
    if name not in seen:
        return name
    n = 2
    while f"{name}_{n}" in seen:
        n += 1
    return f"{name}_{n}"


def _is_excluded(path: str, cfg: dict[str, Any]) -> bool:
    include_paths = cfg.get("INCLUDE_PATHS")
    if include_paths and not any(path.startswith(p) for p in include_paths):
        return True
    return any(path.startswith(p) for p in cfg.get("EXCLUDE_PATHS", []))


def _build_one(
    schema: dict[str, Any], path: str, method: str, operation: dict[str, Any]
) -> ToolSpec:
    op_id = operation.get("operationId") or _fallback_id(method, path)
    name = _sanitize_name(op_id)
    description = (
        operation.get("summary") or operation.get("description") or f"{method} {path}"
    )

    properties: dict[str, Any] = {}
    required: list[str] = []
    params: list[dict[str, str]] = []

    for param in operation.get("parameters", []):
        if "$ref" in param:
            param = resolve_ref(schema, param["$ref"])
        location = param.get("in")
        if location not in ("path", "query"):
            continue
        pname = param["name"]
        prop = dict(param.get("schema") or {"type": "string"})
        if param.get("description"):
            prop["description"] = param["description"]
        properties[pname] = prop
        # Path params are always required; query params honour their flag.
        if location == "path" or param.get("required"):
            required.append(pname)
        params.append({"name": pname, "in": location})

    input_schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        input_schema["required"] = required

    return ToolSpec(
        name=name,
        description=description,
        input_schema=input_schema,
        method=method,
        path=path,
        params=params,
    )


def _sanitize_name(op_id: str) -> str:
    name = _NAME_RE.sub("_", op_id).strip("_")
    return (name or "tool")[:64]


def _fallback_id(method: str, path: str) -> str:
    slug = _NAME_RE.sub("_", path).strip("_")
    return f"{method.lower()}_{slug}"
