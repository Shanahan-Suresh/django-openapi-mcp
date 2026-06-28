"""End-to-end probe: spawn the stdio MCP server and exercise it as a real client.

Run with the venv python from the repo root. Requires the example Django server
to be running on http://127.0.0.1:8000 so tool calls have a live API to hit.
"""

import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLE = os.path.join(REPO, "example")
PYTHON = sys.executable


async def main() -> int:
    params = StdioServerParameters(
        command=PYTHON,
        args=["manage.py", "run_mcp_server", "--transport", "stdio"],
        cwd=EXAMPLE,
        env={**os.environ, "DJANGO_SETTINGS_MODULE": "config.settings"},
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = (await session.list_tools()).tools
            names = sorted(t.name for t in tools)
            print(f"[OK] handshake complete; {len(tools)} tools advertised")
            for t in tools:
                req = t.inputSchema.get("required", [])
                print(f"     - {t.name}  required={req}")

            # Pick the products list tool (no required args) and call it.
            list_tool = next(
                (t for t in tools if "product" in t.name and not t.inputSchema.get("required")),
                None,
            )
            if list_tool is None:
                print("[FAIL] no products-list tool found")
                return 1

            print(f"\n[CALL] {list_tool.name} (no args)")
            result = await session.call_tool(list_tool.name, {})
            text = result.content[0].text
            print(text[:600])
            if "HTTP 200" not in text:
                print("[FAIL] expected HTTP 200 from live API")
                return 1

            # Call with a query-param filter to prove arg -> query mapping.
            if any(
                "in_stock" in (t.inputSchema.get("properties") or {})
                for t in [list_tool]
            ):
                print(f"\n[CALL] {list_tool.name} (in_stock=true)")
                r2 = await session.call_tool(list_tool.name, {"in_stock": True})
                print(r2.content[0].text[:400])

            print("\n[PASS] real MCP client handshake + tool execution succeeded")
            return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
