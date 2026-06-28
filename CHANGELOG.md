# Changelog

## 0.1.0 (unreleased)

Initial release.

- Generate a real MCP server from a Django/DRF OpenAPI schema (via drf-spectacular, in-process).
- Read-only by default: only `GET` endpoints become tools; write methods are opt-in via `INCLUDE_METHODS`.
- Credential passthrough: token / bearer / custom-header auth applied to outgoing requests.
- `INCLUDE_PATHS` / `EXCLUDE_PATHS` filtering.
- Serve over **stdio** (Claude Desktop / Claude Code) and **Streamable HTTP** (`[http]` extra).
- `python manage.py run_mcp_server` management command.
- Runnable `example/` DRF project and test suite.
