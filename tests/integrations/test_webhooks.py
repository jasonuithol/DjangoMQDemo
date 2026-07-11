from typing import Any
from unittest import mock

import pytest
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APIClient

from integrations.models import WebhookEvent

pytestmark = pytest.mark.django_db

SECRET = "test-secret"


@override_settings(PARTNER_WEBHOOK_SECRET=SECRET)
def test_webhook_rejects_bad_secret(api_client: APIClient) -> None:
    resp = api_client.post(
        "/webhooks/partner/",
        {"event": "order.updated"},
        format="json",
        headers={"X-Partner-Secret": "wrong"},
    )

    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
    assert WebhookEvent.objects.count() == 0


@override_settings(PARTNER_WEBHOOK_SECRET=SECRET)
def test_webhook_persists_payload_and_enqueues(
    api_client: APIClient, django_capture_on_commit_callbacks: Any
) -> None:
    with mock.patch("integrations.webhooks.process_webhook_event.delay") as delay:
        with django_capture_on_commit_callbacks(execute=True):
            resp = api_client.post(
                "/webhooks/partner/",
                {"event": "order.updated", "id": "123"},
                format="json",
                headers={"X-Partner-Secret": SECRET},
            )

    assert resp.status_code == status.HTTP_202_ACCEPTED
    event = WebhookEvent.objects.get()
    assert event.payload == {"event": "order.updated", "id": "123"}
    assert not event.processed
    delay.assert_called_once_with(event.pk)
