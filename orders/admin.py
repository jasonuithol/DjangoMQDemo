from django.contrib import admin

from orders.models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin[Order]):
    list_display = ["id", "customer_name", "total_amount", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["customer_name"]
    readonly_fields = ["id", "created_at"]
