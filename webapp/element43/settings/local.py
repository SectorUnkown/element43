# Import base settings
from .base import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

IMAGE_SERVER = '/static/images/icons'

MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
INSTALLED_APPS += ('debug_toolbar',
                  #'devserver',
                  )

DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql_psycopg2",
                "NAME": "element43",
                "USER": "element43",
                "PASSWORD": "element43",
                "HOST": "localhost",
                "PORT": "",
            }
        }

# Memcache settings
MEMCACHE_SERVER = ['127.0.0.1']
MEMCACHE_BINARY = True
MEMCACHE_BEHAVIOUR = {"tcp_nodelay": True,
                      "ketama": True}

INTERNAL_IPS = ('127.0.0.1',)