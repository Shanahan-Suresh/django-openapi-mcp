"""Idempotent data seed — run once to populate the example database."""

import os
import sys

# Allow running as: python seed.py from the example/ directory
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from shop.models import Order, Product

# Products
products_data = [
    {"name": "Mechanical Keyboard", "price": "129.99", "in_stock": True},
    {"name": "USB-C Hub", "price": "49.99", "in_stock": True},
    {"name": "Monitor Stand", "price": "39.99", "in_stock": False},
]

created_products = []
for data in products_data:
    product, created = Product.objects.get_or_create(name=data["name"], defaults=data)
    created_products.append(product)
    status = "created" if created else "already exists"
    print(f"Product '{product.name}': {status}")

# Orders (only if products were available in stock)
in_stock_products = [p for p in created_products if p.in_stock]
if in_stock_products and not Order.objects.exists():
    Order.objects.create(product=in_stock_products[0], quantity=2)
    Order.objects.create(product=in_stock_products[1], quantity=1)
    print("Created 2 sample orders")
else:
    print("Orders already exist or no in-stock products")

print("Seed complete.")
