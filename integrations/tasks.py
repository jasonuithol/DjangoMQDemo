"""Celery tasks — the integration engine.

Contract: tasks receive IDs (never ORM objects), are idempotent, and retry
external failures with backoff. acks_late so a crashed worker redelivers.
"""

import requests
from celery import Task, shared_task
from django.conf import settings

from integrations.client import PartnerClient
from integrations.models import WebhookEvent
from orders.models import Order


@shared_task(bind=True, acks_late=True, max_retries=5, retry_backoff=True)
def sync_order_to_partner(self: Task, order_id: str) -> None:
    order = Order.objects.get(id=order_id)
    if order.status == Order.Status.SYNCED:
        return  # idempotent: already synced, nothing to do

    client = PartnerClient(settings.PARTNER_API_BASE_URL)
    try:
        client.sync_order(
            order_id=str(order.id),
            customer_name=order.customer_name,
            total_amount=str(order.total_amount),
        )
    except requests.RequestException as exc:
        raise self.retry(exc=exc) from exc

    order.status = Order.Status.SYNCED
    order.save(update_fields=["status"])


@shared_task
def process_webhook_event(event_id: int) -> None:
    event = WebhookEvent.objects.get(id=event_id)
    if event.processed:
        return  # idempotent

    # (demo) real processing would branch on event.payload here.
    event.processed = True
    event.save(update_fields=["processed"])
