"""Celery application bootstrap.

Imported by config/__init__.py so the app is available whenever Django starts.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("platform_service")
# Read CELERY_-namespaced settings from Django config.
app.config_from_object("django.conf:settings", namespace="CELERY")
# Discover tasks.py in every installed app.
app.autodiscover_tasks()
