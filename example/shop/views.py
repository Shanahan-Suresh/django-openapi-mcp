from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.routers import DefaultRouter
from rest_framework.viewsets import ModelViewSet

from .models import Order, Product
from .serializers import OrderSerializer, ProductSerializer


class ProductViewSet(ModelViewSet):
    """CRUD endpoints for products."""

    serializer_class = ProductSerializer
    queryset = Product.objects.all()

    def get_queryset(self):
        qs = super().get_queryset()
        in_stock = self.request.query_params.get("in_stock")
        if in_stock is not None:
            qs = qs.filter(in_stock=in_stock.lower() in ("true", "1", "yes"))
        return qs

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="in_stock",
                type=bool,
                location=OpenApiParameter.QUERY,
                description="Filter by stock availability.",
                required=False,
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class OrderViewSet(ModelViewSet):
    """CRUD endpoints for orders."""

    serializer_class = OrderSerializer
    queryset = Order.objects.all()


router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")
router.register("orders", OrderViewSet, basename="order")
