"""Root URL configuration."""

from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from config.health import health
from integrations.webhooks import partner_webhook
from orders.views import OrderViewSet

router = DefaultRouter()
router.register("orders", OrderViewSet, basename="order")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("webhooks/partner/", partner_webhook),
    path("health/", health),
]
