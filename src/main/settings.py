import os
import sys

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

BOUWDOSSIER_PUBLIC_SCOPE = 'BD/P'  # BouwDossiers_Public_Read. Access to anybody with e-mail link
BOUWDOSSIER_READ_SCOPE = 'BD/R'  # BouwDossiers_Read. Access to civil servants of Amsterdam Municipality
BOUWDOSSIER_EXTENDED_SCOPE = 'BD/X'  # BouwDossiers_eXtended. Access civil servants of Amsterdam Municipality with special rights.

WABO_BASE_URL = os.getenv('WABO_BASE_URL', 'https://bwt.hs3-saa-bwt.shcp04.archivingondemand.nl/')

ALLOWED_HOSTS = ['*']

INTERNAL_IPS = ('127.0.0.1', '0.0.0.0')


INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'django_filters',
    'django_extensions',
    'django.contrib.gis',
    'rest_framework',
    'rest_framework_gis',
    'drf_yasg',
    'bouwdossiers',
    'bag',
    'health',
]

if DEBUG:
    INSTALLED_APPS += ('debug_toolbar',)

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'authorization_django.authorization_middleware',
]


# The following JWKS data was obtained in the authz project :  jwkgen -create -alg ES256
# This is a test public/private key def and added for testing .
JWKS_TEST_KEY = """
    {
        "keys": [
            {
                "kty": "EC",
                "key_ops": [
                    "verify",
                    "sign"
                ],
                "kid": "2aedafba-8170-4064-b704-ce92b7c89cc6",
                "crv": "P-256",
                "x": "6r8PYwqfZbq_QzoMA4tzJJsYUIIXdeyPA27qTgEJCDw=",
                "y": "Cf2clfAfFuuCB06NMfIat9ultkMyrMQO9Hd2H7O9ZVE=",
                "d": "N1vu0UQUp0vLfaNeM0EDbl4quvvL6m_ltjoAXXzkI3U="
            }
        ]
    }
"""

if os.getenv('JWKS_USE_TEST_KEY', 'false').lower() == 'true':
    JWKS = JWKS_TEST_KEY
else:
    JWKS = os.environ['PUB_JWKS']

DATAPUNT_AUTHZ = {
    'ALWAYS_OK': False,
    'JWKS': JWKS,
    "JWKS_URL": os.getenv("KEYCLOAK_JWKS_URL"),
    'FORCED_ANONYMOUS_ROUTES': ['/status/health']
}

ROOT_URLCONF = 'main.urls'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'main.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DATABASE_NAME', 'iiif_metadata_server'),
        'USER': os.getenv('DATABASE_USER', 'iiif_metadata_server'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'insecure'),
        'HOST': os.getenv('DATABASE_HOST', 'database'),
        'PORT': os.getenv('DATABASE_PORT', '5432'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/iiif-metadata/static/'
STATIC_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..', 'static'))

# Django Logging settings
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console'
        },

    },
    'root': {
        'handlers': ['console'],
        'level': os.getenv('LOG_LEVEL', 'INFO'),
    },
}


OBJECTSTORE = dict(
    VERSION='2.0',
    AUTHURL='https://identity.stack.cloudvps.com/v2.0',
    TENANT_NAME='BGE000081_BOUWDOSSIERS',
    TENANT_ID='9d078258c1a547c09e0b5f88834554f1',
    USER=os.getenv('OBJECTSTORE_USER', 'bouwdossiers'),
    PASSWORD=os.getenv('BOUWDOSSIERS_OBJECTSTORE_PASSWORD'),
    REGION_NAME='NL',
)

BOUWDOSSIERS_OBJECTSTORE_CONTAINER = os.getenv(
    'BOUWDOSSIERS_OBJECTSTORE_CONTAINER', 'dossiers_acceptance'
)

PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))
DATA_DIR = '/tmp/bouwdossiers'

# SWAGGER
SWAG_PATH = 'acc.bouwdossiers.amsterdam.nl/iiif-metadata-server/docs'

if DEBUG:
    SWAG_PATH = '127.0.0.1:8000/iiif-metadata-server/docs'

SWAGGER_SETTINGS = {
    'exclude_namespaces': [],
    'api_version': '0.1',
    'api_path': '/',

    'enabled_methods': [
        'get',
    ],

    'api_key': '',
    'USE_SESSION_AUTH': False,
    'VALIDATOR_URL': None,

    'is_authenticated': False,
    'is_superuser': False,

    'unauthenticated_user': 'django.contrib.auth.models.AnonymousUser',
    'permission_denied_handler': None,
    'resource_access_handler': None,

    'protocol': 'https' if not DEBUG else '',
    'base_path': SWAG_PATH,

    'info': {
        'contact': 'atlas.basisinformatie@amsterdam.nl',
        'description': 'This is the Bouwdossiers API server.',
        'license': 'Not known yet',
        'termsOfServiceUrl': 'https://data.amsterdam.nl/terms/',
        'title': 'Bouwdossiers',
    },

    'doc_expansion': 'list'
}

HEALTH_MODEL = 'bouwdossiers.Bouwdossier'

SENTRY_DSN = os.getenv('SENTRY_DSN')
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()]
    )


DUMP_DIR = 'mks-dump'

TESTING = len(sys.argv) > 1 and sys.argv[1] == 'test'

REST_FRAMEWORK = dict(
    PAGE_SIZE=100,
    MAX_PAGINATE_BY=100,
    DEFAULT_PAGINATION_CLASS='rest_framework.pagination.PageNumberPagination',

    UNAUTHENTICATED_USER={},
    UNAUTHENTICATED_TOKEN={},

    DEFAULT_AUTHENTICATION_CLASSES=(
        # 'rest_framework.authentication.BasicAuthentication',
        # 'rest_framework.authentication.SessionAuthentication',
    ),

    DEFAULT_RENDERER_CLASSES=(
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer'
    ),
    DEFAULT_FILTER_BACKENDS=(
        # 'rest_framework.filters.DjangoFilterBackend',
        'django_filters.rest_framework.DjangoFilterBackend',
        # 'rest_framework.filters.OrderingFilter',

    ),
    COERCE_DECIMAL_TO_STRING=True,
)

IIIF_BASE_URL = os.getenv('IIIF_BASE_URL', 'https://bouwdossiers.amsterdam.nl/iiif/2/')
