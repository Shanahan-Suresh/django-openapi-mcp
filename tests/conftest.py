"""Shared pytest fixtures for django-openapi-mcp tests."""
import pytest


MINIMAL_SCHEMA = {
    "openapi": "3.0.3",
    "info": {"title": "Test API", "version": "1.0.0"},
    "paths": {
        "/api/products/": {
            "get": {
                "operationId": "products_list",
                "summary": "List all products",
                "parameters": [
                    {
                        "name": "in_stock",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "boolean"},
                        "description": "Filter by stock availability.",
                    }
                ],
                "responses": {"200": {"description": "OK"}},
            },
            "post": {
                "operationId": "products_create",
                "summary": "Create a product",
                "responses": {"201": {"description": "Created"}},
            },
        },
        "/api/products/{id}/": {
            "get": {
                "operationId": "products_retrieve",
                "summary": "Retrieve a product",
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer"},
                    }
                ],
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/api/orders/": {
            "get": {
                "operationId": "orders_list",
                "summary": "List all orders",
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/api/internal/": {
            "get": {
                "operationId": "internal_list",
                "summary": "Internal endpoint",
                "responses": {"200": {"description": "OK"}},
            }
        },
    },
    "components": {
        "parameters": {
            "PageParam": {
                "name": "page",
                "in": "query",
                "required": False,
                "schema": {"type": "integer"},
                "description": "Page number",
            }
        }
    },
}


@pytest.fixture
def minimal_schema():
    """A hand-written minimal OpenAPI schema for unit testing."""
    return MINIMAL_SCHEMA
