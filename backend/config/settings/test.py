"""Test settings for MasteryGrid."""

from .base import *  # noqa: F403

DEBUG = False

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

DATABASES["default"]["TEST"] = {  # noqa: F405
    "NAME": env("TEST_DATABASE_NAME", default="test_masterygrid"),  # noqa: F405
}

