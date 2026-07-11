"""Thin HTTP client for the (fake) partner API.

Boundary object: every outbound call goes through here so tests can stub it
with `responses` and the retry/timeout policy lives in one place.
"""

from dataclasses import dataclass

import requests


@dataclass(frozen=True)
class PartnerSyncResult:
    partner_id: str
    status: str


class PartnerClient:
    def __init__(self, base_url: str, *, timeout: float = 5.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def sync_order(
        self, *, order_id: str, customer_name: str, total_amount: str
    ) -> PartnerSyncResult:
        response = requests.post(
            f"{self._base_url}/orders",
            json={
                "order_id": order_id,
                "customer_name": customer_name,
                "total_amount": total_amount,
            },
            timeout=self._timeout,
        )
        response.raise_for_status()
        data = response.json()
        return PartnerSyncResult(partner_id=str(data["id"]), status=str(data["status"]))
