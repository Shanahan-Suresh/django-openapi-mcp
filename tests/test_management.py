"""Tests for the run_mcp_server management command."""
import pytest


def test_management_command_imports_without_error():
    """The run_mcp_server management command module must be importable."""
    from django_openapi_mcp.management.commands.run_mcp_server import Command
    assert Command is not None


def test_management_command_is_basecommand_subclass():
    """Command must subclass Django's BaseCommand."""
    from django.core.management.base import BaseCommand
    from django_openapi_mcp.management.commands.run_mcp_server import Command
    assert issubclass(Command, BaseCommand)


def test_management_command_has_correct_transport_choices():
    """The --transport argument must offer stdio and http choices."""
    import argparse
    from django_openapi_mcp.management.commands.run_mcp_server import Command
    cmd = Command()
    parser = cmd.create_parser("manage.py", "run_mcp_server")
    # Find the --transport action
    transport_action = next(
        (a for a in parser._actions if "--transport" in getattr(a, "option_strings", [])),
        None,
    )
    assert transport_action is not None, "--transport argument not registered"
    assert set(transport_action.choices) == {"stdio", "http"}
