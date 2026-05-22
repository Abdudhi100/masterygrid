#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys


def main() -> None:
    """Run administrative tasks."""
    if not os.environ.get("DJANGO_SETTINGS_MODULE"):
        django_env = os.environ.get("DJANGO_ENV", "dev")
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"config.settings.{django_env}")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

