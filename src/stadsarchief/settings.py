import os
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from stadsarchief.settings_common import * # noqa F403
from stadsarchief.settings_common import INSTALLED_APPS, DEBUG, DATAPUNT_API_URL
from stadsarchief.settings_databases import LocationKey,\
    get_docker_host,\
    get_database_key,\
    OVERRIDE_HOST_ENV_VAR,\
    OVERRIDE_PORT_ENV_VAR

INSTALLED_APPS += [
    'stadsarchief',
    # 'stadsarchief.importer',
    'stadsarchief.health',
]

ROOT_URLCONF = 'stadsarchief.urls'


WSGI_APPLICATION = 'stadsarchief.wsgi.application'


DATABASE_OPTIONS = {
    LocationKey.docker: {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DATABASE_NAME', 'stadsarchief'),
        'USER': os.getenv('DATABASE_USER', 'stadsarchief'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'insecure'),
        'HOST': 'database',
        'PORT': '5432'
    },
    LocationKey.local: {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DATABASE_NAME', 'stadsarchief'),
        'USER': os.getenv('DATABASE_USER', 'stadsarchief'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'insecure'),
        'HOST': get_docker_host(),
        'PORT': '5412'
    },
    LocationKey.override: {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DATABASE_NAME', 'stadsarchief'),
        'USER': os.getenv('DATABASE_USER', 'stadsarchief'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'insecure'),
        'HOST': os.getenv(OVERRIDE_HOST_ENV_VAR),
        'PORT': os.getenv(OVERRIDE_PORT_ENV_VAR, '5432')
    },
}

DATABASES = {
    'default': DATABASE_OPTIONS[get_database_key()]
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

PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))
DATA_DIR = os.path.abspath(os.path.join(PROJECT_DIR, 'data'))


# SWAGGER
SWAG_PATH = 'acc.api.data.amsterdam.nl/stadsarchief/docs'

if DEBUG:
    SWAG_PATH = '127.0.0.1:8000/stadsarchief/docs'

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
        'description': 'This is the Monumenten API server.',
        'license': 'Not known yet',
        'termsOfServiceUrl': 'https://data.amsterdam.nl/terms/',
        'title': 'Tellus',
    },

    'doc_expansion': 'list',
    'SECURITY_DEFINITIONS': {
        'oauth2': {
            'type': 'oauth2',
            'authorizationUrl': DATAPUNT_API_URL + "oauth2/authorize",
            'flow': 'implicit',
            'scopes': {
                "BD/R": "Bouwdossiers access",
            }
        }
    }
}

HEALTH_MODEL = 'stadsarchief.Bouwdossier'

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

# Bouwdossiers read
SCOPE_BD_R = 'BD/R'

DATAPUNT_AUTHZ = {
    'JWKS': os.getenv('PUB_JWKS', JWKS_TEST_KEY),
    'MIN_SCOPE': SCOPE_BD_R,
    'FORCED_ANONYMOUS_ROUTES': ('/status/', '/handelsregister/static/', '/handelsregister/docs/'),
    'ALWAYS_OK': True,
}


SENTRY_DSN = os.getenv('SENTRY_DSN')
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()]
    )
