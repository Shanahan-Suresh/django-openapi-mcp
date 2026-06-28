# django-openapi-mcp

**Your Django API already documents every endpoint. This turns that documentation into tools an AI assistant can call, automatically, with no hand-written glue.**

If you want an AI assistant (Claude and friends) to *operate* your Django app, fetch a record, run a filtered query, take an action, it needs "tools": machine-readable descriptions of what your API can do. The usual way is to hand-write one for every endpoint, then maintain them forever as the API changes.

`django-openapi-mcp` skips that. It reads the OpenAPI schema [drf-spectacular](https://github.com/tfranzel/drf-spectacular) already generates for your Django REST Framework project and exposes each endpoint as a [Model Context Protocol](https://modelcontextprotocol.io) (MCP) tool. Your schema is the single source of truth: change the API, and the tools change with it. No second place to update.

It's built on the official [`mcp`](https://github.com/modelcontextprotocol/python-sdk) Python SDK, so it speaks the real protocol over **stdio** (Claude Desktop / Claude Code) and **Streamable HTTP** (production).

```
  DRF views ──drf-spectacular──▶ OpenAPI schema ──introspect──▶ MCP tools ──serve──▶  Claude / any MCP client
                                                                          (stdio + Streamable HTTP)
```

---

## Features

- **Your schema is the single source of truth.** Each `operationId` becomes a tool name, parameters become the tool's inputs, descriptions carry through. Define an endpoint once; you never describe it again.
- **Safe by default.** Only read-only `GET` endpoints become tools. Write operations (`POST`/`PUT`/`PATCH`/`DELETE`) are strictly opt-in. Nothing that can change or delete data is exposed to an AI unless you say so.
- **Authentication included.** Real Django APIs are locked down, so the generated tools carry credentials (DRF token, bearer/JWT, or a custom header) through to your endpoints. Configure it once; it applies to every call.
- **Zero config to start.** If drf-spectacular already works in your project, so does this.
- **Not tied to any one AI.** Built on the official SDK over stdio and Streamable HTTP. Anything that speaks MCP (Claude Desktop, Claude Code, your own agent loop) can call the tools. No model or vendor lock-in.

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

You need DRF and drf-spectacular configured. If you're doing DRF, you almost certainly already do. Then add one app and one settings block:

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

That's the whole setup. Now run the server:

```bash
python manage.py run_mcp_server --transport stdio        # for Claude Desktop / Code
python manage.py run_mcp_server --transport http --port 8800   # Streamable HTTP at /mcp
```

Two things happen in two places. The schema is read **in-process** by drf-spectacular when the server starts (no extra HTTP round-trip, no self-call). Tool *execution* hits your live API at `BASE_URL`. So your API server needs to be running before an AI actually calls a tool, but not just to list them.

## Connect a client

Any MCP-compatible client can launch the server and call the generated tools. With Claude Desktop, open **Settings → Developer → Edit Config**. That opens the correct `claude_desktop_config.json` for your install (don't hand-navigate to it; the Microsoft Store build redirects the path). Add:

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

Restart the client and your endpoints show up as tools. Every other client connects the same way: Claude Code via `claude mcp add`, a custom agent over stdio, or Streamable HTTP at `/mcp` for a deployed server. Want to confirm it works before wiring up any client? The [`example/`](example/) project ships a runnable probe script and works with the MCP Inspector. See [`example/README.md`](example/README.md). For the full Claude Desktop walkthrough, see [`docs/claude-desktop.md`](docs/claude-desktop.md).

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

Read-only is the default for a reason. An AI with `DELETE` access is a bad day waiting to happen. When you actually want write tools, opt in explicitly:

```python
DJANGO_OPENAPI_MCP = {
    "INCLUDE_METHODS": ["GET", "POST"],   # exposes create endpoints too
}
```

---

## Try the example

The fastest way to see the whole thing work is the runnable demo in [`example/`](example/): a tiny shop API (products + orders, with an `in_stock` filter). Full walkthrough in [`example/README.md`](example/README.md). The short version:

```bash
cd example
python manage.py migrate
python seed.py                       # a few sample products & orders
python manage.py runserver           # terminal 1: the API
python manage.py run_mcp_server      # terminal 2: the MCP server (stdio)
```

You get four tools (`products_list`, `products_retrieve`, `orders_list`, `orders_retrieve`), and the `in_stock` query-param filter shows how a tool argument maps straight through to a query string.

---

## How it works

Three steps, and the source is laid out to match them:

1. **Introspect:** `drf_spectacular.generators.SchemaGenerator` produces the OpenAPI 3 document in-process.
2. **Generate:** each operation becomes a tool: `operationId` → name, `summary`/`description` → description, path + query parameters → a JSON Schema (`$ref`s resolved, path params marked required).
3. **Serve:** the official SDK's low-level `Server` advertises the tools (`list_tools`) and runs them (`call_tool`) by mapping arguments onto an HTTP request to `BASE_URL`, with auth attached.

The source mirrors that pipeline:

- **`src/django_openapi_mcp/introspect.py`:** get the OpenAPI schema in-process via drf-spectacular's `SchemaGenerator`, with a URL fallback and full `$ref` resolution.
- **`src/django_openapi_mcp/tools.py`:** turn each OpenAPI operation into a tool spec (`operationId` → name, parameters mapped to JSON Schema, collision handling for duplicate names).
- **`src/django_openapi_mcp/server.py`:** build the MCP server on the SDK's low-level `Server`, wiring `list_tools` and `call_tool` to execute requests against the live API at `BASE_URL`.
- **`src/django_openapi_mcp/transport.py`:** serve over stdio (Claude Desktop) and Streamable HTTP (production).
- **`src/django_openapi_mcp/conf.py`** / **`auth.py`:** config defaults (safe-by-default GET-only) and credential passthrough to every outbound request.

---

## Related projects

Generating AI tools from an OpenAPI spec is nothing new. Several projects already cover this ground. If you want a maintained dependency rather than a readable reference, start here:

- [drf-mcp](https://pypi.org/project/drf-mcp/): a maintained, DRF-focused MCP package.
- [openapi-to-mcp](https://pypi.org/project/openapi-to-mcp/), [openapi-mcp-generator](https://pypi.org/project/openapi-mcp-generator/): generic OpenAPI → MCP converters.
- [FastMCP](https://github.com/jlowin/fastmcp): has native OpenAPI support.

## License

MIT
