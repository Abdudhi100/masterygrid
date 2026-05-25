"""Test settings for MasteryGrid."""

from .base import *  # noqa: F403

DEBUG = False

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

TEST_DATABASE_NAME = env("TEST_DATABASE_NAME", default=None)  # noqa: F405

if TEST_DATABASE_NAME:
    DATABASES["default"]["TEST"] = {"NAME": TEST_DATABASE_NAME}  # noqa: F405
elif DATABASES["default"]["ENGINE"] != "django.db.backends.sqlite3":  # noqa: F405
    DATABASES["default"]["TEST"] = {"NAME": "test_masterygrid"}  # noqa: F405
