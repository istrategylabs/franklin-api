import dj_database_url

from .base import *
from config.settings import setup_sentry_logging

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
    }
}


DATABASES['default'] = dj_database_url.config()


INSTALLED_APPS += ('raven.contrib.django.raven_compat',)

SENTRY_DSN = os.environ['SENTRY_DSN']

# Settings for Raven (Sentry reporting service)
RAVEN_CONFIG = {
    'dsn': SENTRY_DSN,
}

setup_sentry_logging(LOGGING)
