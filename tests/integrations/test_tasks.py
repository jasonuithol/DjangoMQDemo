import json
from unittest import mock

import pytest
import responses
from celery.exceptions import Retry

from integrations.tasks import sync_order_to_partner
from orders.factories import OrderFactory
from orders.models import Order

pytestmark = pytest.mark.django_db

PARTNER_URL = "https://partner.example.com/orders"


@responses.activate
def test_task_syncs_order_and_calls_partner() -> None:
    order = OrderFactory(status=Order.Status.PENDING)
    responses.add(responses.POST, PARTNER_URL, json={"id": "p1", "status": "ok"}, status=200)

    sync_order_to_partner.apply(args=[str(order.id)])

    order.refresh_from_db()
    assert order.status == Order.Status.SYNCED

    body = responses.calls[0].request.body
    assert body is not None
    assert json.loads(body)["order_id"] == str(order.id)


@responses.activate
def test_task_retries_on_partner_error() -> None:
    order = OrderFactory(status=Order.Status.PENDING)
    responses.add(responses.POST, PARTNER_URL, status=500)

    # Mock retry so it raises immediately instead of scheduling real retries.
    with mock.patch.object(sync_order_to_partner, "retry", side_effect=Retry) as retry:
        try:
            sync_order_to_partner.apply(args=[str(order.id)])
        except Retry:
            pass

    assert retry.called
    order.refresh_from_db()
    assert order.status == Order.Status.PENDING


@responses.activate
def test_task_is_idempotent_when_already_synced() -> None:
    order = OrderFactory(status=Order.Status.SYNCED)

    # No responses registered: any outbound call would raise ConnectionError.
    sync_order_to_partner.apply(args=[str(order.id)])

    assert len(responses.calls) == 0
    order.refresh_from_db()
    assert order.status == Order.Status.SYNCED
