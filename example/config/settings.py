"""Django settings for the django-openapi-mcp example project."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-example-dev-key-do-not-use-in-production"

DEBUG = True

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "drf_spectacular",
    "django_openapi_mcp",
    "shop",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Shop API",
    "DESCRIPTION": "Example DRF API demonstrating django-openapi-mcp",
    "VERSION": "1.0.0",
}

# django-openapi-mcp configuration
# BASE_URL: where the generated MCP tools send HTTP requests
# AUTH: uncomment and configure for authenticated APIs
# INCLUDE_METHODS: add "POST", "PUT", "PATCH", "DELETE" to enable write tools
DJANGO_OPENAPI_MCP = {
    "BASE_URL": "http://127.0.0.1:8000",
    # Don't expose the schema/docs endpoints themselves as tools.
    "EXCLUDE_PATHS": ["/api/schema"],
    # "AUTH": {"type": "token", "token": "your-token-here", "scheme": "Token"},
    # "INCLUDE_METHODS": ["GET", "POST", "PUT", "PATCH", "DELETE"],
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
