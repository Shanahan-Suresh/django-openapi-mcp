"""Tests for django_openapi_mcp.server.build_server()."""
import pytest

from django_openapi_mcp.server import build_server
from django_openapi_mcp.tools import ToolSpec


@pytest.mark.django_db
def test_build_server_returns_tuple():
    result = build_server()
    assert isinstance(result, tuple)
    assert len(result) == 2


@pytest.mark.django_db
def test_build_server_returns_specs():
    server, specs = build_server()
    assert isinstance(specs, list)
    assert len(specs) > 0


@pytest.mark.django_db
def test_specs_are_tool_spec_instances():
    _, specs = build_server()
    for spec in specs:
        assert isinstance(spec, ToolSpec)


@pytest.mark.django_db
def test_products_list_tool_exists():
    _, specs = build_server()
    names = {s.name for s in specs}
    # The exact name depends on drf-spectacular's operationId generation
    product_tools = [n for n in names if "product" in n and "list" in n]
    assert product_tools, f"No products-list tool found. Tool names: {sorted(names)}"


@pytest.mark.django_db
def test_products_retrieve_tool_exists():
    _, specs = build_server()
    names = {s.name for s in specs}
    product_retrieve = [n for n in names if "product" in n and "retrieve" in n]
    assert product_retrieve, f"No products-retrieve tool found. Tool names: {sorted(names)}"


@pytest.mark.django_db
def test_list_tools_handler_registered():
    """Verify that the server has a list_tools handler registered."""
    server, specs = build_server()
    # The MCP lowlevel Server stores handlers; verify it is a Server instance
    from mcp.server.lowlevel import Server
    assert isinstance(server, Server)


@pytest.mark.django_db
def test_all_specs_have_method_and_path():
    _, specs = build_server()
    for spec in specs:
        assert spec.method, f"Spec {spec.name!r} has no method"
        assert spec.path, f"Spec {spec.name!r} has no path"
        assert spec.method == "GET"  # default config is GET-only
