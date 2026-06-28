"""Tests for django_openapi_mcp.introspect.get_schema()."""

import pytest

from django_openapi_mcp.introspect import get_schema


@pytest.mark.django_db
def test_get_schema_returns_dict():
    schema = get_schema()
    assert isinstance(schema, dict)


@pytest.mark.django_db
def test_schema_has_paths():
    schema = get_schema()
    assert "paths" in schema
    assert isinstance(schema["paths"], dict)


@pytest.mark.django_db
def test_schema_contains_products_endpoint():
    schema = get_schema()
    paths = schema.get("paths", {})
    product_paths = [p for p in paths if "product" in p]
    assert product_paths, f"No products endpoint found. Paths: {list(paths)}"


@pytest.mark.django_db
def test_schema_contains_orders_endpoint():
    schema = get_schema()
    paths = schema.get("paths", {})
    order_paths = [p for p in paths if "order" in p]
    assert order_paths, f"No orders endpoint found. Paths: {list(paths)}"


@pytest.mark.django_db
def test_schema_has_openapi_version():
    schema = get_schema()
    assert "openapi" in schema
    assert schema["openapi"].startswith("3.")
