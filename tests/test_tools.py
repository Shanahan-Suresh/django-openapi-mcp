"""Unit tests for django_openapi_mcp.tools.build_tool_specs."""

from django.test import override_settings

from django_openapi_mcp.tools import build_tool_specs


def _get_tool(specs, name):
    return next((s for s in specs if s.name == name), None)


def test_get_operations_included_by_default(minimal_schema):
    specs = build_tool_specs(minimal_schema)
    names = {s.name for s in specs}
    assert "products_list" in names
    assert "products_retrieve" in names
    assert "orders_list" in names


def test_post_excluded_by_default(minimal_schema):
    specs = build_tool_specs(minimal_schema)
    names = {s.name for s in specs}
    assert "products_create" not in names


@override_settings(DJANGO_OPENAPI_MCP={"INCLUDE_METHODS": ["GET", "POST"]})
def test_post_included_when_configured(minimal_schema):
    specs = build_tool_specs(minimal_schema)
    names = {s.name for s in specs}
    assert "products_create" in names
    assert "products_list" in names


@override_settings(DJANGO_OPENAPI_MCP={"INCLUDE_METHODS": ["POST"]})
def test_only_post_when_get_excluded(minimal_schema):
    specs = build_tool_specs(minimal_schema)
    names = {s.name for s in specs}
    assert "products_create" in names
    assert "products_list" not in names


def test_operationid_is_tool_name(minimal_schema):
    specs = build_tool_specs(minimal_schema)
    tool = _get_tool(specs, "products_list")
    assert tool is not None
    assert tool.name == "products_list"


def test_special_chars_sanitized():
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
    # spaces, !, etc. with underscores: "foo-bar baz!qux" -> "foo-bar_baz_qux"
    assert specs[0].name == "foo-bar_baz_qux"


def test_fallback_name_when_no_operationid():
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
    assert len(specs) == 1
    assert specs[0].name  # not empty


def test_duplicate_operationids_are_deduplicated():
    schema = {
        "paths": {
            "/api/a/": {"get": {"operationId": "dup", "responses": {}}},
            "/api/b/": {"get": {"operationId": "dup", "responses": {}}},
        }
    }
    specs = build_tool_specs(schema)
    names = sorted(s.name for s in specs)
    assert names == ["dup", "dup_2"]


def test_path_param_is_required(minimal_schema):
    specs = build_tool_specs(minimal_schema)
    tool = _get_tool(specs, "products_retrieve")
    assert tool is not None
    assert "id" in tool.input_schema.get("required", [])


def test_path_param_in_properties(minimal_schema):
    specs = build_tool_specs(minimal_schema)
    tool = _get_tool(specs, "products_retrieve")
    assert "id" in tool.input_schema["properties"]
    assert tool.input_schema["properties"]["id"]["type"] == "integer"


def test_path_param_tracked_in_params_list(minimal_schema):
    specs = build_tool_specs(minimal_schema)
    tool = _get_tool(specs, "products_retrieve")
    path_params = [p for p in tool.params if p["in"] == "path"]
    assert any(p["name"] == "id" for p in path_params)


def test_optional_query_param_not_required(minimal_schema):
    specs = build_tool_specs(minimal_schema)
    tool = _get_tool(specs, "products_list")
    assert tool is not None
    required = tool.input_schema.get("required", [])
    assert "in_stock" not in required


def test_optional_query_param_in_properties(minimal_schema):
    specs = build_tool_specs(minimal_schema)
    tool = _get_tool(specs, "products_list")
    assert "in_stock" in tool.input_schema["properties"]


def test_required_query_param_is_in_required():
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


def test_xquik_openapi31_search_query_parameters():
    schema = {
        "openapi": "3.1.0",
        "info": {"title": "Xquik API", "version": "1.0"},
        "servers": [{"url": "https://xquik.com"}],
        "components": {
            "securitySchemes": {
                "apiKey": {"type": "apiKey", "name": "x-api-key", "in": "header"}
            }
        },
        "paths": {
            "/api/v1/x/tweets/search": {
                "get": {
                    "operationId": "searchTweets",
                    "summary": "Search X posts",
                    "security": [{"apiKey": []}],
                    "parameters": [
                        {
                            "name": "q",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                        {
                            "name": "queryType",
                            "in": "query",
                            "schema": {
                                "type": "string",
                                "enum": ["Latest", "Top"],
                                "default": "Latest",
                            },
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "schema": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 200,
                                "default": 20,
                            },
                        },
                    ],
                    "responses": {"200": {"description": "Search results"}},
                }
            }
        },
    }

    specs = build_tool_specs(schema)
    tool = _get_tool(specs, "searchTweets")

    assert tool is not None
    assert tool.description == "Search X posts"
    assert tool.method == "GET"
    assert tool.path == "/api/v1/x/tweets/search"
    assert "q" in tool.input_schema.get("required", [])
    assert tool.input_schema["properties"]["queryType"]["enum"] == ["Latest", "Top"]
    assert tool.input_schema["properties"]["queryType"]["default"] == "Latest"
    assert tool.input_schema["properties"]["limit"]["maximum"] == 200
    assert {"name": "q", "in": "query"} in tool.params


def test_ref_parameter_resolved(minimal_schema):
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


@override_settings(DJANGO_OPENAPI_MCP={"EXCLUDE_PATHS": ["/api/internal/"]})
def test_excluded_path_not_in_specs(minimal_schema):
    specs = build_tool_specs(minimal_schema)
    names = {s.name for s in specs}
    assert "internal_list" not in names


@override_settings(DJANGO_OPENAPI_MCP={"EXCLUDE_PATHS": ["/api/internal/"]})
def test_non_excluded_paths_still_present(minimal_schema):
    specs = build_tool_specs(minimal_schema)
    names = {s.name for s in specs}
    assert "products_list" in names
    assert "orders_list" in names


@override_settings(DJANGO_OPENAPI_MCP={"INCLUDE_PATHS": ["/api/products/"]})
def test_include_paths_filters_others(minimal_schema):
    specs = build_tool_specs(minimal_schema)
    names = {s.name for s in specs}
    assert "products_list" in names
    assert "orders_list" not in names
    assert "internal_list" not in names
