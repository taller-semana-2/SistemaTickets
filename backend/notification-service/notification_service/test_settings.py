"""
Test settings for notification-service.
Uses SQLite in-memory instead of PostgreSQL for fast local testing.
"""

import os

# Set required env vars before importing main settings
os.environ.setdefault('NOTIFICATION_SERVICE_SECRET_KEY', 'test-secret-key-for-testing')

from notification_service.settings import *  # noqa: F401, F403

# Override database to use SQLite in-memory
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

SECRET_KEY = 'test-secret-key-for-testing'
DEBUG = True
