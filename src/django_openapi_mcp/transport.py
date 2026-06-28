"""Serve a built MCP server over stdio or Streamable HTTP."""

from __future__ import annotations

from contextlib import asynccontextmanager

from mcp.server.lowlevel import Server


async def run_stdio(server: Server) -> None:
    """Serve over stdio (the transport Claude Desktop / Claude Code use)."""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


def run_http(
    server: Server,
    host: str = "127.0.0.1",
    port: int = 8800,
    json_response: bool = True,
) -> None:
    """Serve over Streamable HTTP at ``/mcp`` (requires the ``http`` extra)."""
    import uvicorn
    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
    from starlette.applications import Starlette
    from starlette.routing import Mount

    manager = StreamableHTTPSessionManager(
        app=server, json_response=json_response, stateless=True
    )

    @asynccontextmanager
    async def lifespan(_app: Starlette):
        async with manager.run():
            yield

    async def handle_mcp(scope, receive, send):
        await manager.handle_request(scope, receive, send)

    app = Starlette(routes=[Mount("/mcp", app=handle_mcp)], lifespan=lifespan)
    uvicorn.run(app, host=host, port=port)
