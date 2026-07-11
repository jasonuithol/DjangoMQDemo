"""Test settings — Celery runs inline so no broker is needed."""

from .base import *  # noqa: F401,F403

DEBUG = False

# Run Celery tasks eagerly (in-process) and surface exceptions to the test.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Faster hashing in tests.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
