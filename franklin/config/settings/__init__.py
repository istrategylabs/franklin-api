

def setup_sentry_logging(LOGGING):

    # Add the handler
    LOGGING['handlers'].update({
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler'
        },
    })

    # Add the root logger
    LOGGING.update({
        'root': {
            'level': 'WARNING',
            'handlers': ['sentry'],
        },
    })

    # Update the Loggers
    LOGGING['loggers'].update({
        'raven': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'sentry.errors': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
    })
