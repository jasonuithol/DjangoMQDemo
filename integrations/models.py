from django.db import models


class WebhookEvent(models.Model):
    """Raw inbound partner webhook, persisted fast and processed async."""

    payload = models.JSONField()
    processed = models.BooleanField(default=False)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-received_at"]
        indexes = [models.Index(fields=["processed"])]

    def __str__(self) -> str:
        return f"WebhookEvent {self.pk} (processed={self.processed})"
