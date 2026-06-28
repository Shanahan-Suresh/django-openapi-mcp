"""``python manage.py run_mcp_server`` — serve the generated MCP server."""

from __future__ import annotations

import argparse
from typing import Any

import anyio
from django.core.management.base import BaseCommand

from django_openapi_mcp import transport
from django_openapi_mcp.server import build_server


class Command(BaseCommand):
    help = "Run an MCP server auto-generated from this project's OpenAPI schema."

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--transport",
            choices=["stdio", "http"],
            default="stdio",
            help="Transport to serve on (default: stdio).",
        )
        parser.add_argument(
            "--host",
            default="127.0.0.1",
            help="Host to bind for the http transport (default: 127.0.0.1).",
        )
        parser.add_argument(
            "--port",
            type=int,
            default=8800,
            help="Port to bind for the http transport (default: 8800).",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        server, specs = build_server()
        # NOTE: in stdio mode, stdout carries the MCP protocol — never print
        # diagnostics there. Always log to stderr.
        self.stderr.write(f"django-openapi-mcp: generated {len(specs)} tool(s)")

        if options["transport"] == "stdio":
            anyio.run(transport.run_stdio, server)
        else:
            self.stderr.write(
                f"Serving Streamable HTTP at http://{options['host']}:{options['port']}/mcp"
            )
            transport.run_http(server, options["host"], options["port"])
