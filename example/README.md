# example/ — the django-openapi-mcp demo project

A tiny DRF shop API with two resources — **Products** and **Orders** — wired up as MCP tools. It exists so you can see the full pipeline working locally: DRF views → drf-spectacular schema → MCP tool list → Claude.

Products have an `in_stock` boolean filter on the list endpoint, which demonstrates how a query parameter defined in the schema maps through to a tool argument automatically.

With the current settings (`EXCLUDE_PATHS: ["/api/schema"]`, `INCLUDE_METHODS: ["GET"]`) the server generates **4 read-only tools**: `products_list`, `products_retrieve`, `orders_list`, `orders_retrieve`.

---

## Prerequisites

- Python 3.11+
- The repo cloned locally

---

## Step-by-step

All commands below assume you're in the repo root (`django-openapi-mcp/`).

**1. Create and activate a virtual environment**

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

**2. Install the package and example dependencies**

```bash
pip install -e ".[http]"
pip install -r example/requirements.txt   # if present, otherwise the editable install covers it
```

If there's no `requirements.txt` in `example/`, the editable install from the repo root is sufficient — the example's `manage.py` uses the same environment.

**3. Set up the database and seed data**

```bash
cd example
python manage.py migrate
python seed.py
```

`seed.py` creates a handful of sample products (some in stock, some not) and a couple of orders so the list endpoints return something interesting.

**4. Start the API server (terminal 1)**

```bash
# still inside example/
python manage.py runserver
```

Leave this running. The MCP server proxies tool calls to `http://127.0.0.1:8000`, so the API must be up.

**5. Start the MCP server (terminal 2)**

```bash
# inside example/, same venv activated
python manage.py run_mcp_server --transport stdio
```

You'll see a line on stderr reporting how many tools were registered (should be 4). The server then waits for MCP messages on stdin — that's the stdio transport Claude Desktop uses.

---

## See the tools in action

Pick whichever client you like — they all talk to the same stdio server. Keep the API from step 4 running, since tool calls hit it.

### Quickest: the bundled probe (no extra tools)

From the **repo root**, with the venv active and the API running:

```bash
python tests/mcp_e2e_probe.py
```

It spawns the MCP server, completes the handshake as a real MCP client, lists the generated tools, and calls `products_list` (including the `in_stock` filter) against your live API — printing the results. Pure Python, nothing else to install. This is also the easiest thing to screenshot.

(There's a matching `tests/mcp_http_probe.py` for the Streamable HTTP transport — start the server with `--transport http --port 8800` first.)

### Visual: MCP Inspector

The official inspector gives you a browser UI to list and call tools. With the venv active, from this `example/` directory:

```bash
npx @modelcontextprotocol/inspector python manage.py run_mcp_server --transport stdio
```

Requires Node. Click a tool, fill in args, run it.

### In an LLM client

Any MCP client launches the server the same way — the command `python manage.py run_mcp_server --transport stdio` with `cwd` set to this `example/` folder and `DJANGO_SETTINGS_MODULE=config.settings`.

- **Claude Desktop:** open **Settings → Developer → Edit Config**. That button opens (and creates if missing) the correct `claude_desktop_config.json` for your install — don't hunt for it by hand, because the Microsoft Store build keeps it under `…\Packages\Claude_*\LocalCache\Roaming\Claude\`, not the plain `%APPDATA%\Claude\`. Paste the snippet from [`../docs/claude-desktop.md`](../docs/claude-desktop.md), save, and fully restart Claude Desktop.
- **Claude Code:** from this `example/` directory, run `claude mcp add django-demo -- python manage.py run_mcp_server --transport stdio`.

Then ask the model:

- "List all products that are in stock."
- "Get the details of product 1."
- "Show me all orders."

The `in_stock` parameter on `products_list` is passed as a query string automatically.

> A stdio MCP server can't be added from a chat message — the client starts the server process itself, so it needs the command/cwd configured first (the Edit Config button or `claude mcp add` above). Once configured, the tools just appear.
