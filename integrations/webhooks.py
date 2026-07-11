"""Inbound partner webhook: verify secret, persist raw payload, ack fast."""

import hmac

from django.conf import settings
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from integrations.models import WebhookEvent
from integrations.tasks import process_webhook_event


@api_view(["POST"])
@permission_classes([AllowAny])
def partner_webhook(request: Request) -> Response:
    secret = request.headers.get("X-Partner-Secret", "")
    if not hmac.compare_digest(secret, settings.PARTNER_WEBHOOK_SECRET):
        return Response({"detail": "invalid secret"}, status=status.HTTP_401_UNAUTHORIZED)

    event = WebhookEvent.objects.create(payload=request.data)
    transaction.on_commit(lambda: process_webhook_event.delay(event.pk))
    return Response({"status": "accepted"}, status=status.HTTP_202_ACCEPTED)
