"""ASGI config for MasteryGrid."""

import os

django_env = os.environ.get("DJANGO_ENV", "dev")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"config.settings.{django_env}")

from django.core.asgi import get_asgi_application

application = get_asgi_application()

