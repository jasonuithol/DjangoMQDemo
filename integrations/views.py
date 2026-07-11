from rest_framework import viewsets

from integrations.models import WebhookEvent
from integrations.serializers import WebhookEventSerializer


class WebhookEventViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only list/retrieve of received webhook events (newest first)."""

    queryset = WebhookEvent.objects.all()
    serializer_class = WebhookEventSerializer
