# Changelog

## 0.1.0 (unreleased)

Initial release.

- Generate a real MCP server from a Django/DRF OpenAPI schema (in-process via drf-spectacular, no HTTP self-call).
- Read-only by default: only `GET` endpoints become tools; write methods are opt-in via `INCLUDE_METHODS`.
- Credential passthrough: token / bearer / custom-header auth attached to every outgoing request.
- Scope what's exposed with `INCLUDE_PATHS` / `EXCLUDE_PATHS` filtering.
- Serve over **stdio** (Claude Desktop / Claude Code) and **Streamable HTTP** (the `[http]` extra).
- `python manage.py run_mcp_server` management command.
- Runnable `example/` DRF project plus a full test suite.
