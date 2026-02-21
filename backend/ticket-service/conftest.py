"""
Conftest raíz para pytest-django.
Configura SQLite en memoria para pruebas locales.
"""
import os

os.environ.setdefault("TICKET_SERVICE_SECRET_KEY", "test-secret-key")


def pytest_configure(config):
    """Override database to use SQLite in-memory for tests."""
    os.environ["DJANGO_SETTINGS_MODULE"] = "ticket_service.settings"

    import django
    from django.conf import settings

    settings.DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
    django.setup()
