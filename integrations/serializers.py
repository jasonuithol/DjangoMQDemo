from rest_framework import serializers

from integrations.models import WebhookEvent


class WebhookEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookEvent
        fields = ["id", "payload", "processed", "received_at"]
