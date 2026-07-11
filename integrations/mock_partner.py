"""A local stand-in for the partner API.

Served by the app itself (DEBUG only) so the sync task can succeed end-to-end in
development without a real third party. Not wired up in production.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response


@api_view(["POST"])
@permission_classes([AllowAny])
def mock_partner_orders(request: Request) -> Response:
    order_id = request.data.get("order_id", "unknown")
    return Response(
        {"id": f"partner-{order_id}", "status": "ok"},
        status=status.HTTP_200_OK,
    )
