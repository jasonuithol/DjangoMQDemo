"""Root URL configuration."""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from config.frontend import index
from config.health import health
from integrations.mock_partner import mock_partner_orders
from integrations.views import WebhookEventViewSet
from integrations.webhooks import partner_webhook
from orders.views import OrderViewSet

router = DefaultRouter()
router.register("orders", OrderViewSet, basename="order")
router.register("webhook-events", WebhookEventViewSet, basename="webhook-event")

urlpatterns = [
    path("", index),
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("webhooks/partner/", partner_webhook),
    path("health/", health),
]

if settings.DEBUG:
    # Local fake partner so sync_order_to_partner can succeed end-to-end.
    # The client posts to "<PARTNER_API_BASE_URL>/orders" (no trailing slash).
    urlpatterns += [path("mock-partner/orders", mock_partner_orders)]
