#!/usr/bin/env python
"""Django management utility for the Philippine Election Network Observatory."""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "election_observatory.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django is not installed. Run: python -m pip install -r requirements_dashboard.txt"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
