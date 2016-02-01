import dj_database_url

from .base import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
    }
}


DATABASES['default'] = dj_database_url.config()
