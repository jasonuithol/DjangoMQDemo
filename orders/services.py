"""Business logic for the orders app.

Plain functions — the seam where views/tasks delegate. No DI container; call
these directly and mock them (or the boundaries they touch) in tests.
"""

from decimal import Decimal

from django.db import transaction

from integrations.tasks import sync_order_to_partner
from orders.models import Order


def create_order(*, customer_name: str, total_amount: Decimal) -> Order:
    """Create an Order and enqueue the partner sync once the row is committed."""
    order = Order.objects.create(customer_name=customer_name, total_amount=total_amount)
    # Enqueue only after the surrounding transaction commits, so the worker never
    # races ahead of a row that isn't visible yet.
    transaction.on_commit(lambda: sync_order_to_partner.delay(str(order.id)))
    return order
