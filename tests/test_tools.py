"""Unit tests for django_openapi_mcp.tools.build_tool_specs."""
import pytest
from django.test import override_settings

from django_openapi_mcp.tools import build_tool_specs


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_tool(specs, name):
    return next((s for s in specs if s.name == name), None)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGetOperationsBecomeTools:
    def test_get_operations_included_by_default(self, minimal_schema):
        specs = build_tool_specs(minimal_schema)
        names = {s.name for s in specs}
        assert "products_list" in names
        assert "products_retrieve" in names
        assert "orders_list" in names

    def test_post_excluded_by_default(self, minimal_schema):
        specs = build_tool_specs(minimal_schema)
        names = {s.name for s in specs}
        assert "products_create" not in names

    @override_settings(DJANGO_OPENAPI_MCP={"INCLUDE_METHODS": ["GET", "POST"]})
    def test_post_included_when_configured(self, minimal_schema):
        specs = build_tool_specs(minimal_schema)
        names = {s.name for s in specs}
        assert "products_create" in names
        assert "products_list" in names

    @override_settings(DJANGO_OPENAPI_MCP={"INCLUDE_METHODS": ["POST"]})
    def test_only_post_when_get_excluded(self, minimal_schema):
        specs = build_tool_specs(minimal_schema)
        names = {s.name for s in specs}
        assert "products_create" in names
        assert "products_list" not in names


class TestOperationIdBecomesToolName:
    def test_operationid_is_tool_name(self, minimal_schema):
        specs = build_tool_specs(minimal_schema)
        tool = _get_tool(specs, "products_list")
        assert tool is not None
        assert tool.name == "products_list"

    def test_special_chars_sanitized(self):
        schema = {
            "paths": {
                "/api/foo/": {
                    "get": {
                        "operationId": "foo-bar baz!qux",
                        "summary": "Test",
                        "responses": {},
                    }
                }
            }
        }
        specs = build_tool_specs(schema)
        # The sanitizer keeps hyphens (valid in tool names) and replaces
        # spaces, !, etc. with underscores: "foo-bar baz!qux" → "foo-bar_baz_qux"
        assert specs[0].name == "foo-bar_baz_qux"

    def test_fallback_name_when_no_operationid(self):
        schema = {
            "paths": {
                "/api/widgets/": {
                    "get": {
                        "summary": "No operation ID here",
                        "responses": {},
                    }
                }
            }
        }
        specs = build_tool_specs(schema)
        # Fallback: get__api_widgets_ or similar
        assert len(specs) == 1
        assert specs[0].name  # not empty


class TestPathParameters:
    def test_path_param_is_required(self, minimal_schema):
        specs = build_tool_specs(minimal_schema)
        tool = _get_tool(specs, "products_retrieve")
        assert tool is not None
        assert "id" in tool.input_schema.get("required", [])

    def test_path_param_in_properties(self, minimal_schema):
        specs = build_tool_specs(minimal_schema)
        tool = _get_tool(specs, "products_retrieve")
        assert "id" in tool.input_schema["properties"]
        assert tool.input_schema["properties"]["id"]["type"] == "integer"

    def test_path_param_tracked_in_params_list(self, minimal_schema):
        specs = build_tool_specs(minimal_schema)
        tool = _get_tool(specs, "products_retrieve")
        path_params = [p for p in tool.params if p["in"] == "path"]
        assert any(p["name"] == "id" for p in path_params)


class TestQueryParameters:
    def test_optional_query_param_not_required(self, minimal_schema):
        specs = build_tool_specs(minimal_schema)
        tool = _get_tool(specs, "products_list")
        assert tool is not None
        required = tool.input_schema.get("required", [])
        assert "in_stock" not in required

    def test_optional_query_param_in_properties(self, minimal_schema):
        specs = build_tool_specs(minimal_schema)
        tool = _get_tool(specs, "products_list")
        assert "in_stock" in tool.input_schema["properties"]

    def test_required_query_param_is_in_required(self):
        schema = {
            "paths": {
                "/api/search/": {
                    "get": {
                        "operationId": "search",
                        "summary": "Search",
                        "parameters": [
                            {
                                "name": "q",
                                "in": "query",
                                "required": True,
                                "schema": {"type": "string"},
                            }
                        ],
                        "responses": {},
                    }
                }
            }
        }
        specs = build_tool_specs(schema)
        tool = _get_tool(specs, "search")
        assert "q" in tool.input_schema.get("required", [])


class TestRefResolution:
    def test_ref_parameter_resolved(self, minimal_schema):
        schema = dict(minimal_schema)
        schema["paths"] = {
            "/api/paged/": {
                "get": {
                    "operationId": "paged_list",
                    "summary": "Paged list",
                    "parameters": [{"$ref": "#/components/parameters/PageParam"}],
                    "responses": {},
                }
            }
        }
        specs = build_tool_specs(schema)
        tool = _get_tool(specs, "paged_list")
        assert tool is not None
        assert "page" in tool.input_schema["properties"]
        assert tool.input_schema["properties"]["page"]["type"] == "integer"


class TestExcludePaths:
    @override_settings(DJANGO_OPENAPI_MCP={"EXCLUDE_PATHS": ["/api/internal/"]})
    def test_excluded_path_not_in_specs(self, minimal_schema):
        specs = build_tool_specs(minimal_schema)
        names = {s.name for s in specs}
        assert "internal_list" not in names

    @override_settings(DJANGO_OPENAPI_MCP={"EXCLUDE_PATHS": ["/api/internal/"]})
    def test_non_excluded_paths_still_present(self, minimal_schema):
        specs = build_tool_specs(minimal_schema)
        names = {s.name for s in specs}
        assert "products_list" in names
        assert "orders_list" in names

    @override_settings(DJANGO_OPENAPI_MCP={"INCLUDE_PATHS": ["/api/products/"]})
    def test_include_paths_filters_others(self, minimal_schema):
        specs = build_tool_specs(minimal_schema)
        names = {s.name for s in specs}
        assert "products_list" in names
        assert "orders_list" not in names
        assert "internal_list" not in names
