"""Smoke test the Streamable HTTP transport against a running server on :8800."""

import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main() -> int:
    async with streamablehttp_client("http://127.0.0.1:8800/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = (await session.list_tools()).tools
            print(f"[OK] HTTP handshake; {len(tools)} tools")
            result = await session.call_tool("products_list", {})
            text = result.content[0].text
            print(text[:200])
            ok = "HTTP 200" in text
            print("[PASS]" if ok else "[FAIL]", "streamable HTTP transport")
            return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
