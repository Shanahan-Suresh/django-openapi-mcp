"""Tests for the run_mcp_server management command."""

import pytest
from django.core.management.base import BaseCommand, CommandError

from django_openapi_mcp.management.commands.run_mcp_server import Command


def test_management_command_is_basecommand_subclass():
    """Command must subclass Django's BaseCommand."""
    assert issubclass(Command, BaseCommand)


def test_transport_defaults_to_stdio():
    parser = Command().create_parser("manage.py", "run_mcp_server")
    opts = parser.parse_args([])
    assert opts.transport == "stdio"
    assert opts.host == "127.0.0.1"
    assert opts.port == 8800


def test_http_transport_with_host_and_port_parses():
    parser = Command().create_parser("manage.py", "run_mcp_server")
    opts = parser.parse_args(
        ["--transport", "http", "--host", "0.0.0.0", "--port", "9000"]
    )
    assert opts.transport == "http"
    assert opts.host == "0.0.0.0"
    assert opts.port == 9000


def test_invalid_transport_choice_rejected():
    parser = Command().create_parser("manage.py", "run_mcp_server")
    with pytest.raises(CommandError):
        parser.parse_args(["--transport", "ftp"])
