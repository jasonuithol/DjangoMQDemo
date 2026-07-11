"""Serves the single-page hands-on UI (templates/index.html)."""

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def index(request: HttpRequest) -> HttpResponse:
    # Expose the dev webhook secret so the UI can pre-fill it (dev convenience only).
    return render(request, "index.html", {"partner_secret": settings.PARTNER_WEBHOOK_SECRET})
