from typing import Any

import pytest
from rest_framework.test import APIClient

from orders.factories import OrderFactory

pytestmark = pytest.mark.django_db


def test_order_list_query_count_is_constant(
    api_client: APIClient, django_assert_num_queries: Any
) -> None:
    """The list endpoint must not issue per-row queries (anti-N+1 guard).

    PageNumberPagination = one COUNT + one page SELECT, regardless of row count.
    """
    OrderFactory.create_batch(10)

    with django_assert_num_queries(2):
        resp = api_client.get("/api/orders/")

    assert resp.status_code == 200
    assert resp.json()["count"] == 10
