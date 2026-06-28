# example/: the django-openapi-mcp demo project

A tiny DRF shop API with two resources (**Products** and **Orders**) wired up as MCP tools. Run it locally and you can watch the full pipeline end to end in a couple of minutes: DRF views → drf-spectacular schema → MCP tool list → an AI client calling your live API.

Products have an `in_stock` boolean filter on the list endpoint. It's a small detail, but it shows a query parameter from the schema flowing through to a tool argument without any extra work on your part.

With the settings shipped here (`EXCLUDE_PATHS: ["/api/schema"]`, `INCLUDE_METHODS: ["GET"]`), the server generates exactly **4 read-only tools**: `products_list`, `products_retrieve`, `orders_list`, `orders_retrieve`.

---

## Prerequisites

- Python 3.10+
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
```

That editable install pulls in everything the example needs (Django, DRF, drf-spectacular). The example's `manage.py` runs in the same environment.

**3. Set up the database and seed data**

```bash
cd example
python manage.py migrate
python seed.py
```

`seed.py` adds a handful of sample products (some in stock, some not) and a couple of orders, so the list endpoints return something worth looking at.

**4. Start the API server (terminal 1)**

```bash
# still inside example/
python manage.py runserver
```

Leave this running. The MCP server forwards every tool call to `http://127.0.0.1:8000`, so the API has to be up for calls to land.

**5. Start the MCP server (terminal 2)**

```bash
# inside example/, same venv activated
python manage.py run_mcp_server --transport stdio
```

You'll see a line on stderr reporting how many tools were registered (should say 4). After that the server waits for MCP messages on stdin. That's the stdio transport Claude Desktop uses.

---

## See the tools in action

Pick whichever client you like; they all talk to the same stdio server. Keep the API from step 4 running, because every tool call hits it.

### Quickest: the bundled probe (no extra tools)

From the **repo root**, with the venv active and the API running:

```bash
python tests/mcp_e2e_probe.py
```

It spawns the MCP server, completes the handshake as a real MCP client, lists the generated tools, then calls `products_list` (including the `in_stock` filter) against your live API and prints what comes back. Pure Python, nothing else to install. Easiest thing in the repo to screenshot.

(There's a matching `tests/mcp_http_probe.py` for the Streamable HTTP transport. Start the server with `--transport http --port 8800` first.)

### Visual: MCP Inspector

The official inspector gives you a browser UI to list and call tools. With the venv active, from this `example/` directory:

```bash
npx @modelcontextprotocol/inspector python manage.py run_mcp_server --transport stdio
```

Requires Node. Click a tool, fill in args, run it.

### In an LLM client

Any MCP client launches the server the same way: `python manage.py run_mcp_server --transport stdio` with `cwd` set to this `example/` folder and `DJANGO_SETTINGS_MODULE=config.settings`.

- **Claude Desktop:** open **Settings → Developer → Edit Config**. That button opens (and creates if missing) the correct `claude_desktop_config.json` for your install. Don't hunt for it by hand; the Microsoft Store build keeps it under `…\Packages\Claude_*\LocalCache\Roaming\Claude\`, not the plain `%APPDATA%\Claude\`. Paste the snippet from [`../docs/claude-desktop.md`](../docs/claude-desktop.md), save, and fully restart Claude Desktop.
- **Claude Code:** from this `example/` directory, run `claude mcp add django-demo -- python manage.py run_mcp_server --transport stdio`.

Then ask the model:

- "List all products that are in stock."
- "Get the details of product 1."
- "Show me all orders."

The `in_stock` parameter on `products_list` is passed as a query string automatically.

> A stdio MCP server can't be added from a chat message. The client starts the server process itself, so it needs the command/cwd configured first (the Edit Config button or `claude mcp add` above). Once configured, the tools just appear.
