from decimal import Decimal

from rest_framework import serializers

from orders.models import Order


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["id", "customer_name", "total_amount", "status", "created_at"]
        read_only_fields = ["id", "status", "created_at"]

    def validate_total_amount(self, value: Decimal) -> Decimal:
        if value <= 0:
            raise serializers.ValidationError("total_amount must be greater than 0.")
        return value
