"""Unit tests for request construction and response formatting in server.py."""

import httpx

from django_openapi_mcp.server import _build_request, _format_response
from django_openapi_mcp.tools import ToolSpec


def _spec(**overrides):
    base = dict(
        name="products_retrieve",
        description="Retrieve a product",
        input_schema={"type": "object", "properties": {}},
        method="GET",
        path="/api/products/{id}/",
        params=[{"name": "id", "in": "path"}],
    )
    base.update(overrides)
    return ToolSpec(**base)


def test_path_param_substituted_into_url():
    spec = _spec()
    method, url, query, _ = _build_request(spec, {"id": 7}, {"BASE_URL": "http://x"})
    assert method == "GET"
    assert url == "http://x/api/products/7/"
    assert query == {}


def test_query_param_collected_separately():
    spec = _spec(
        path="/api/products/",
        params=[{"name": "in_stock", "in": "query"}],
    )
    _, url, query, _ = _build_request(
        spec, {"in_stock": True}, {"BASE_URL": "http://x"}
    )
    assert url == "http://x/api/products/"
    assert query == {"in_stock": True}


def test_base_url_trailing_slash_is_normalised():
    spec = _spec(path="/api/orders/", params=[])
    _, url, _, _ = _build_request(spec, {}, {"BASE_URL": "http://x/"})
    assert url == "http://x/api/orders/"


def test_auth_headers_merged_in():
    spec = _spec(path="/api/orders/", params=[])
    cfg = {"BASE_URL": "http://x", "AUTH": {"type": "bearer", "token": "t"}}
    _, _, _, headers = _build_request(spec, {}, cfg)
    assert headers["Accept"] == "application/json"
    assert headers["Authorization"] == "Bearer t"


def test_unknown_argument_is_ignored():
    spec = _spec(path="/api/orders/", params=[])
    _, url, query, _ = _build_request(spec, {"bogus": 1}, {"BASE_URL": "http://x"})
    assert url == "http://x/api/orders/"
    assert query == {}


def test_format_response_pretty_prints_json():
    resp = httpx.Response(200, json={"id": 1, "name": "Keyboard"})
    text = _format_response(resp, "GET", "http://x/api/products/1/")
    assert text.startswith("HTTP 200 GET http://x/api/products/1/")
    assert '"name": "Keyboard"' in text


def test_format_response_falls_back_to_text_for_non_json():
    resp = httpx.Response(500, text="Internal Server Error")
    text = _format_response(resp, "GET", "http://x/api/products/")
    assert "HTTP 500 GET" in text
    assert "Internal Server Error" in text
