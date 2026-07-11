import pytest
from rest_framework import status
from rest_framework.test import APIClient

from orders.factories import OrderFactory
from orders.models import Order

pytestmark = pytest.mark.django_db


def test_create_order_returns_201_and_persists(api_client: APIClient) -> None:
    resp = api_client.post(
        "/api/orders/",
        {"customer_name": "Ada", "total_amount": "42.50"},
        format="json",
    )
    assert resp.status_code == status.HTTP_201_CREATED
    assert Order.objects.filter(customer_name="Ada").count() == 1


@pytest.mark.parametrize("amount", ["0", "0.00", "-1", "-99.99"])
def test_create_order_rejects_non_positive_amount(api_client: APIClient, amount: str) -> None:
    resp = api_client.post(
        "/api/orders/",
        {"customer_name": "Bad", "total_amount": amount},
        format="json",
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "total_amount" in resp.json()
    assert not Order.objects.exists()


def test_list_filters_by_status(api_client: APIClient) -> None:
    OrderFactory(status=Order.Status.PENDING)
    OrderFactory(status=Order.Status.SYNCED)

    resp = api_client.get("/api/orders/", {"status": "synced"})

    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert body["count"] == 1
    assert body["results"][0]["status"] == "synced"


def test_list_has_pagination_shape(api_client: APIClient) -> None:
    OrderFactory.create_batch(3)

    resp = api_client.get("/api/orders/")

    body = resp.json()
    assert set(body) == {"count", "next", "previous", "results"}
    assert body["count"] == 3
