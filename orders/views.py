from django.db.models import QuerySet
from rest_framework import mixins, viewsets
from rest_framework.serializers import BaseSerializer

from orders.models import Order
from orders.serializers import OrderSerializer
from orders.services import create_order


class OrderViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """List/retrieve/create orders. Thin — creation delegates to services."""

    serializer_class = OrderSerializer
    queryset = Order.objects.all()

    def get_queryset(self) -> QuerySet[Order]:
        qs = super().get_queryset()
        status = self.request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs

    def perform_create(self, serializer: BaseSerializer[Order]) -> None:
        serializer.instance = create_order(
            customer_name=serializer.validated_data["customer_name"],
            total_amount=serializer.validated_data["total_amount"],
        )
