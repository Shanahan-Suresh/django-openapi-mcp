# Connecting to Claude Desktop

`django-openapi-mcp` serves a standard stdio MCP server, so Claude Desktop can
launch it directly.

## 1. Open the config file

The reliable way on any platform and install type: in Claude Desktop, open
**Settings → Developer → Edit Config**. That opens — and creates if it doesn't
exist — the correct `claude_desktop_config.json` and reveals it in your file
manager. Use this and you never have to guess the path.

If you'd rather find it manually:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows (standalone installer):** `%APPDATA%\Claude\claude_desktop_config.json`
- **Windows (Microsoft Store build):** the path above is redirected — the file
  actually lives under
  `%LOCALAPPDATA%\Packages\Claude_<id>\LocalCache\Roaming\Claude\claude_desktop_config.json`.
  The `<id>` varies per machine, so the Edit Config button is far easier.

If the file is empty or missing, create it with just the `mcpServers` block below.

## 2. Add a server entry

Point `command` at the Python interpreter from the virtualenv where your Django
project and `django-openapi-mcp` are installed, and `cwd` at the directory
containing `manage.py` (the `example/` subdirectory of this repo when using the
bundled demo, or your own project root).

### Using the bundled example project

```json
{
  "mcpServers": {
    "shop-api": {
      "command": "/path/to/django-openapi-mcp/.venv/bin/python",
      "args": ["manage.py", "run_mcp_server", "--transport", "stdio"],
      "cwd": "/path/to/django-openapi-mcp/example",
      "env": { "DJANGO_SETTINGS_MODULE": "config.settings" }
    }
  }
}
```

On Windows use backslash paths and `Scripts\python.exe`:

```json
{
  "mcpServers": {
    "shop-api": {
      "command": "C:\\path\\to\\django-openapi-mcp\\.venv\\Scripts\\python.exe",
      "args": ["manage.py", "run_mcp_server", "--transport", "stdio"],
      "cwd": "C:\\path\\to\\django-openapi-mcp\\example",
      "env": { "DJANGO_SETTINGS_MODULE": "config.settings" }
    }
  }
}
```

### Using your own Django project

```json
{
  "mcpServers": {
    "my-django-api": {
      "command": "/path/to/your/.venv/bin/python",
      "args": ["manage.py", "run_mcp_server", "--transport", "stdio"],
      "cwd": "/path/to/your/django/project",
      "env": { "DJANGO_SETTINGS_MODULE": "myproject.settings" }
    }
  }
}
```

## 3. Make sure the API is reachable

Tool *execution* calls your live API at `BASE_URL` (from `DJANGO_OPENAPI_MCP` in
`settings.py`), so that server needs to be running before you invoke tools.
Schema generation happens in-process when the MCP server starts — the API server
is not required for tool registration, only for tool execution.

For the bundled example, run the API first in a separate terminal:

```bash
cd example
python manage.py migrate    # first time only
python manage.py runserver  # keep this running
```

## 4. Restart Claude Desktop

Quit and relaunch Claude Desktop after editing the config. Your endpoints now
appear as tools. With the bundled example you should see four tools:
`products_list`, `products_retrieve`, `orders_list`, `orders_retrieve`.

Ask Claude something like "list all products that are in stock" — it will call
`products_list` with `in_stock=true` automatically.

## Troubleshooting

- **No tools appear / server fails to start:** run the same command in a terminal
  to see the error — `python manage.py run_mcp_server --transport stdio`. It
  prints the generated tool count to stderr on startup.
- **Tools appear but return connection errors:** confirm `BASE_URL` in your
  `DJANGO_OPENAPI_MCP` settings matches the running API server address, and that
  any configured `AUTH` credentials are valid.
- **Wrong tool count:** check `EXCLUDE_PATHS` and `INCLUDE_METHODS` in your
  `DJANGO_OPENAPI_MCP` settings — by default only `GET` endpoints are exposed.

## The stdio footgun

**Never write to stdout** in any code that runs while the MCP server is active in
stdio mode. Stdout carries the MCP wire protocol; anything else written there
corrupts the message stream and will confuse or crash the client.

This applies to `print()`, `sys.stdout.write()`, and any Django middleware or
signal handler that might emit output. Always log to stderr:

```python
import sys
print("debug info", file=sys.stderr)  # safe
# or use Django's logging framework, which goes to stderr by default
```

The management command itself follows this rule — `self.stderr.write(...)` for
diagnostics, never `self.stdout.write(...)`.
