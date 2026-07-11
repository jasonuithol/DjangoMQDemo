from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from unittest import mock

import pytest
from freezegun import freeze_time

from orders.models import Order
from orders.services import create_order

pytestmark = pytest.mark.django_db


def test_create_order_persists_pending_row() -> None:
    order = create_order(customer_name="Ada", total_amount=Decimal("10.00"))

    assert Order.objects.filter(pk=order.pk).exists()
    assert order.status == Order.Status.PENDING


def test_create_order_enqueues_sync_on_commit(
    django_capture_on_commit_callbacks: Any,
) -> None:
    with mock.patch("orders.services.sync_order_to_partner.delay") as delay:
        with django_capture_on_commit_callbacks(execute=True):
            order = create_order(customer_name="Ada", total_amount=Decimal("10.00"))

    delay.assert_called_once_with(str(order.id))


@freeze_time("2026-01-01T12:00:00Z")
def test_create_order_stamps_created_at() -> None:
    order = create_order(customer_name="Ada", total_amount=Decimal("1.00"))

    assert order.created_at == datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
