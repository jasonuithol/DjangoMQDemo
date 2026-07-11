import pytest
from rest_framework.test import APIClient

from orders.factories import OrderFactory
from orders.models import Order


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def order(db: None) -> Order:
    return OrderFactory()
