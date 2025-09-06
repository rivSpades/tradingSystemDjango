"""
Debug settings for Django Debug Toolbar
Add this to your settings.py or create a separate debug settings file
"""

# Import your main settings
from .settings import *

# Enable debug mode
DEBUG = True

# Add debug toolbar to installed apps
INSTALLED_APPS += [
    'debug_toolbar',
]

# Add debug toolbar middleware
MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

# Configure debug toolbar
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# Debug toolbar configuration
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
    'INTERCEPT_REDIRECTS': False,
}

# Logging configuration for debugging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'DEBUG',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'backtesting': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'portfolio': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
