"""WSGI config for MasteryGrid."""

import os

django_env = os.environ.get("DJANGO_ENV", "dev")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"config.settings.{django_env}")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

