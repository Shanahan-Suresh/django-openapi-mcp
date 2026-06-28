# Connecting to Claude Desktop

`django-openapi-mcp` serves a standard stdio MCP server. Claude Desktop can launch and talk to it directly. Here's the five-minute setup.

## 1. Open the config file

The reliable path on every platform and install type: in Claude Desktop, open
**Settings → Developer → Edit Config**. That opens the correct
`claude_desktop_config.json` (creating it if it doesn't exist yet) and reveals it
in your file manager. Use that button and you never have to guess where the file
lives.

If you'd rather find it manually:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows (standalone installer):** `%APPDATA%\Claude\claude_desktop_config.json`
- **Windows (Microsoft Store build):** the path above is redirected. The file
  actually lives under
  `%LOCALAPPDATA%\Packages\Claude_<id>\LocalCache\Roaming\Claude\claude_desktop_config.json`.
  The `<id>` varies per machine, so the Edit Config button is far easier.

If the file is empty or missing, create it with just the `mcpServers` block below.

## 2. Add a server entry

Two fields do the real work: point `command` at the Python interpreter from the
virtualenv where your Django project and `django-openapi-mcp` are installed, and
`cwd` at the directory that holds `manage.py` (the repo's `example/` subdirectory
for the bundled demo, or your own project root).

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

Remember the split. Tool *execution* calls your live API at `BASE_URL` (set in
`DJANGO_OPENAPI_MCP` in `settings.py`), so that server has to be running before
you invoke a tool. Schema generation happens in-process when the MCP server
starts, so the API server isn't needed to *register* tools, only to *run* them.

For the bundled example, run the API first in a separate terminal:

```bash
cd example
python manage.py migrate    # first time only
python manage.py runserver  # keep this running
```

## 4. Restart Claude Desktop

Fully quit and relaunch Claude Desktop after editing the config. A reload isn't
enough. Your endpoints now show up as tools; with the bundled example you'll see
four: `products_list`, `products_retrieve`, `orders_list`, `orders_retrieve`.

Ask in plain English ("list all products that are in stock") and Claude calls
`products_list` with `in_stock=true` on its own.

## Troubleshooting

- **No tools appear / server fails to start:** run the same command in a terminal
  to see the error: `python manage.py run_mcp_server --transport stdio`. It
  prints the generated tool count to stderr on startup.
- **Tools appear but return connection errors:** confirm `BASE_URL` in your
  `DJANGO_OPENAPI_MCP` settings matches the running API server address, and that
  any configured `AUTH` credentials are valid.
- **Wrong tool count:** check `EXCLUDE_PATHS` and `INCLUDE_METHODS` in your
  `DJANGO_OPENAPI_MCP` settings. By default only `GET` endpoints are exposed.

## The stdio gotcha

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

The management command itself follows this rule: `self.stderr.write(...)` for
diagnostics, never `self.stdout.write(...)`.
