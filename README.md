# django-openapi-mcp

**Point it at your Django REST API's OpenAPI schema, get a real MCP server. No per-endpoint tool definitions.**

`django-openapi-mcp` introspects the OpenAPI schema that [drf-spectacular](https://github.com/tfranzel/drf-spectacular) already generates for your Django REST Framework project and exposes each endpoint as a [Model Context Protocol](https://modelcontextprotocol.io) tool. Your schema is the single source of truth — when the API changes, the tools change with it.

It's built on the official [`mcp`](https://github.com/modelcontextprotocol/python-sdk) Python SDK, so it speaks the real protocol over **stdio** (Claude Desktop / Claude Code) and **Streamable HTTP** (production).

```
  DRF views ──drf-spectacular──▶ OpenAPI schema ──introspect──▶ MCP tools ──serve──▶  Claude / any MCP client
                                                                          (stdio + Streamable HTTP)
```

---

## Features

- **Schema-driven.** `operationId` → tool name, parameters → tool input schema, descriptions carried through. Hand-writing one tool per endpoint doesn't scale; this removes that maintenance cost.
- **Safe by default.** Only read-only `GET` endpoints become tools. Write operations (`POST`/`PUT`/`PATCH`/`DELETE`) are strictly opt-in — nothing destructive is exposed unless you ask for it.
- **Auth passthrough.** Real Django APIs are authenticated. Generated tools carry credentials (DRF token, bearer/JWT, or a custom header) through to the underlying endpoints. Configured once, applied to every call.
- **Zero-config.** If drf-spectacular works in your project, this works.
- **Works with any MCP client.** Built on the official SDK over stdio + Streamable HTTP — any LLM or AI agent that speaks MCP (Claude Desktop, Claude Code, your own agent loop, …) can call the tools. Nothing is tied to a specific model or vendor.

---

## Install

```bash
pip install "git+https://github.com/Shanahan-Suresh/django-openapi-mcp"                              # core
pip install "django-openapi-mcp[http] @ git+https://github.com/Shanahan-Suresh/django-openapi-mcp"   # + Streamable HTTP transport
```

To explore the bundled demo instead, clone the repo and follow [`example/README.md`](example/README.md):

```bash
git clone https://github.com/Shanahan-Suresh/django-openapi-mcp
cd django-openapi-mcp/example
```

## Setup

Your project needs DRF and drf-spectacular configured (you likely already have this):

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "rest_framework",
    "drf_spectacular",
    "django_openapi_mcp",
]

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

DJANGO_OPENAPI_MCP = {
    "BASE_URL": "http://127.0.0.1:8000",   # where generated tools send requests
}
```

That's it. Run the server:

```bash
python manage.py run_mcp_server --transport stdio        # for Claude Desktop / Code
python manage.py run_mcp_server --transport http --port 8800   # Streamable HTTP at /mcp
```

The schema is generated **in-process** by drf-spectacular — no extra HTTP round-trip — while tool *execution* calls your live API at `BASE_URL`, so the API server needs to be running.

## Connect a client

Any MCP-compatible client can launch the server and call the generated tools. With Claude Desktop, open **Settings → Developer → Edit Config** — that opens the correct `claude_desktop_config.json` for your install (don't hand-navigate to it; the Microsoft Store build redirects the path) — and add:

```json
{
  "mcpServers": {
    "my-django-api": {
      "command": "/path/to/your/.venv/bin/python",
      "args": ["manage.py", "run_mcp_server", "--transport", "stdio"],
      "cwd": "/path/to/your/django/project",
      "env": { "DJANGO_SETTINGS_MODULE": "config.settings" }
    }
  }
}
```

Restart the client and your endpoints appear as tools. Other clients connect the same way — Claude Code via `claude mcp add`, a custom agent over stdio, or Streamable HTTP at `/mcp` for a deployed server. To verify the server with no client at all, the [`example/`](example/) project ships a runnable probe script and works with the MCP Inspector — see [`example/README.md`](example/README.md). See [`docs/claude-desktop.md`](docs/claude-desktop.md) for the full Claude Desktop walkthrough.

## Configuration

All keys live under `DJANGO_OPENAPI_MCP` in `settings.py`:

| Key               | Default                 | Purpose                                                         |
| ----------------- | ----------------------- | --------------------------------------------------------------- |
| `BASE_URL`        | `http://localhost:8000` | Where generated tools send HTTP requests.                       |
| `INCLUDE_METHODS` | `["GET"]`               | HTTP methods to expose. Add write methods to opt in.            |
| `EXCLUDE_PATHS`   | `[]`                    | Path prefixes to skip (e.g. `["/api/schema"]`).                 |
| `INCLUDE_PATHS`   | `None`                  | If set, only these path prefixes are exposed.                   |
| `AUTH`            | `None`                  | Credential passthrough (see below).                             |
| `SCHEMA_URL`      | `None`                  | Fetch the schema over HTTP instead of generating it in-process. |
| `SERVER_NAME`     | `"django-openapi-mcp"`  | Name advertised to MCP clients.                                 |
| `TIMEOUT`         | `30`                    | HTTP timeout (seconds).                                         |

### Authentication

```python
DJANGO_OPENAPI_MCP = {
    "AUTH": {"type": "token", "token": "...", "scheme": "Token"},   # Authorization: Token ...
    # {"type": "bearer", "token": "..."}                            # Authorization: Bearer ...
    # {"type": "header", "name": "X-API-Key", "value": "..."}       # custom header
}
```

### Enabling write operations (opt-in)

```python
DJANGO_OPENAPI_MCP = {
    "INCLUDE_METHODS": ["GET", "POST"],   # exposes create endpoints too
}
```

---

## Try the example

A runnable DRF project lives in [`example/`](example/) — a tiny shop (products + orders, with an `in_stock` filter). See [`example/README.md`](example/README.md) for the full walkthrough.

```bash
cd example
python manage.py migrate
python seed.py                       # a few sample products & orders
python manage.py runserver           # terminal 1 — the API
python manage.py run_mcp_server      # terminal 2 — the MCP server (stdio)
```

It exposes `products_list`, `products_retrieve`, `orders_list`, `orders_retrieve`, including an `in_stock` query-param filter that demonstrates argument → query mapping.

---

## How it works

1. **Introspect** — `drf_spectacular.generators.SchemaGenerator` produces the OpenAPI 3 document in-process.
2. **Generate** — each operation becomes a tool: `operationId` → name, `summary`/`description` → description, path + query parameters → a JSON Schema (`$ref`s resolved, path params marked required).
3. **Serve** — the official SDK's low-level `Server` advertises the tools (`list_tools`) and executes them (`call_tool`) by mapping arguments onto an HTTP request to `BASE_URL`, with auth attached.

The source mirrors that pipeline:

- **`src/django_openapi_mcp/introspect.py`** — get the OpenAPI schema: in-process via drf-spectacular's `SchemaGenerator`, with a URL fallback and full `$ref` resolution.
- **`src/django_openapi_mcp/tools.py`** — turn each OpenAPI operation into a tool spec: `operationId` → name, parameters mapped to JSON Schema, collision handling for duplicate names.
- **`src/django_openapi_mcp/server.py`** — build the MCP server on the SDK's low-level `Server`, wiring `list_tools` and `call_tool` to execute requests against the live API at `BASE_URL`.
- **`src/django_openapi_mcp/transport.py`** — serve over stdio (Claude Desktop) and Streamable HTTP (production).
- **`src/django_openapi_mcp/conf.py`** / **`auth.py`** — config defaults (safe-by-default GET-only) and credential passthrough to every outbound request.

---

## Related projects

Generating LLM tools from an OpenAPI spec is a common pattern, and other tools cover adjacent ground:

- [drf-mcp](https://pypi.org/project/drf-mcp/) — a maintained DRF-focused MCP package.
- [openapi-to-mcp](https://pypi.org/project/openapi-to-mcp/), [openapi-mcp-generator](https://pypi.org/project/openapi-mcp-generator/) — generic OpenAPI → MCP converters.
- [FastMCP](https://github.com/jlowin/fastmcp) — has native OpenAPI support.

## License

MIT
