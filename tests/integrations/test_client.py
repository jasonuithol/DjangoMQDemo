import json

import pytest
import requests
import responses

from integrations.client import PartnerClient

PARTNER_URL = "https://partner.example.com/orders"


@responses.activate
def test_sync_order_parses_success_and_sends_expected_body() -> None:
    responses.add(
        responses.POST,
        PARTNER_URL,
        json={"id": "partner-1", "status": "ok"},
        status=200,
    )

    client = PartnerClient("https://partner.example.com")
    result = client.sync_order(order_id="o1", customer_name="Ada", total_amount="42.50")

    assert result.partner_id == "partner-1"
    assert result.status == "ok"

    body = responses.calls[0].request.body
    assert body is not None
    assert json.loads(body) == {
        "order_id": "o1",
        "customer_name": "Ada",
        "total_amount": "42.50",
    }


@responses.activate
def test_sync_order_raises_on_server_error() -> None:
    responses.add(responses.POST, PARTNER_URL, status=500)

    client = PartnerClient("https://partner.example.com")
    with pytest.raises(requests.HTTPError):
        client.sync_order(order_id="o1", customer_name="Ada", total_amount="1.00")


@responses.activate
def test_sync_order_propagates_connection_error() -> None:
    responses.add(responses.POST, PARTNER_URL, body=requests.ConnectionError("boom"))

    client = PartnerClient("https://partner.example.com")
    with pytest.raises(requests.RequestException):
        client.sync_order(order_id="o1", customer_name="Ada", total_amount="1.00")
