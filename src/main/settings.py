import json
import os
import sys

from corsheaders.defaults import default_headers
from csp.constants import NONCE, SELF
from opencensus.trace import config_integration

from main.utils_azure_insights import (
    create_azure_log_handler_config,
    create_azure_trace_config,
)

from .azure_settings import Azure

azure = Azure()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

APP_NAME = os.getenv("APP_NAME", "iiif-metadata-server")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

BOUWDOSSIER_PUBLIC_SCOPE = (
    "BD/P"  # BouwDossiers_Public_Read. Access to anybody with e-mail link
)
BOUWDOSSIER_READ_SCOPE = (
    "BD/R"  # BouwDossiers_Read. Access to civil servants of Amsterdam Municipality
)
BOUWDOSSIER_EXTENDED_SCOPE = "BD/X"  # BouwDossiers_eXtended. Access civil servants of Amsterdam Municipality with special rights.

# list of WABO url starts in 'bestanden' -> these starts get removed
WABO_BASE_URL = [
    "J:/INZAGEDOCS/Datapunt/",
    "https://bwt.hs3-saa-bwt.shcp04.archivingondemand.nl/",
    "https://conversiestraatwabo.amsterdam.nl/webDAV/",
]
WABO_ENABLED = os.getenv("WABO_ENABLED", "false").lower() == "true"

ALLOWED_HOSTS = ["*"]

if CORS_DOMAINS := os.getenv("CORS_DOMAINS", ""):
    CORS_ALLOWED_ORIGINS = CORS_DOMAINS.split(",")
    CORS_ALLOW_METHODS = ("GET",)
    CORS_ALLOW_HEADERS = [
        *default_headers,
        "X-Api-Key",
    ]

INTERNAL_IPS = ("127.0.0.1", "0.0.0.0")


INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "django_filters",
    "django_extensions",
    "django.contrib.gis",
    "rest_framework",
    "rest_framework_gis",
    "drf_yasg",
    "bouwdossiers",
    "bag",
    "importer",
    "health",
    "corsheaders",
    "csp",
]

MIDDLEWARE = [
    "csp.middleware.CSPMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "authorization_django.authorization_middleware",
]

if DEBUG:
    INSTALLED_APPS += ("debug_toolbar",)
    MIDDLEWARE += ("debug_toolbar.middleware.DebugToolbarMiddleware",)


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

USE_JWKS_TEST_KEY = os.getenv("USE_JWKS_TEST_KEY", "false").lower() == "true"
PUB_JWKS = JWKS_TEST_KEY if USE_JWKS_TEST_KEY else os.getenv("PUB_JWKS")


DATAPUNT_AUTHZ = {
    "ALWAYS_OK": False,
    "JWKS": PUB_JWKS,
    "JWKS_URL": os.getenv("KEYCLOAK_JWKS_URL"),
    "FORCED_ANONYMOUS_ROUTES": ["/status/health"],
}

ROOT_URLCONF = "main.urls"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "main.wsgi.application"


DATABASE_HOST = os.getenv("DATABASE_HOST", "database")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "dev")
DATABASE_OPTIONS = {"sslmode": "allow", "connect_timeout": 5}

# Check if we are using Azure Database for PostgreSQL, if so additional options are required
if DATABASE_HOST and DATABASE_HOST.endswith(".azure.com"):
    DATABASE_PASSWORD = azure.auth.db_password
    DATABASE_OPTIONS["sslmode"] = "require"

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.getenv("DATABASE_NAME", "dev"),
        "USER": os.getenv("DATABASE_USER", "dev"),
        "PASSWORD": DATABASE_PASSWORD,
        "HOST": DATABASE_HOST,
        "PORT": os.getenv("DATABASE_PORT", "5432"),
        "OPTIONS": DATABASE_OPTIONS,
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = "/iiif-metadata/static/"
STATIC_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", "static"))

# Django Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING").upper()
DJANGO_LOG_LEVEL = os.getenv("DJANGO_LOG_LEVEL", "WARNING").upper()

base_log_fmt = {"time": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s"}
log_fmt = base_log_fmt.copy()
log_fmt["message"] = "%(message)s"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "root": {
        "level": LOG_LEVEL,
        "handlers": ["console"],
    },
    "formatters": {
        "json": {"format": json.dumps(log_fmt)},
    },
    "handlers": {
        "console": {
            "level": LOG_LEVEL,
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "loggers": {
        "bag": {
            "level": LOG_LEVEL,
            "handlers": ["console"],
            "propagate": False,
        },
        "bouwdossiers": {
            "level": LOG_LEVEL,
            "handlers": ["console"],
            "propagate": False,
        },
        "importer": {
            "level": LOG_LEVEL,
            "handlers": ["console"],
            "propagate": False,
        },
        "main": {
            "level": LOG_LEVEL,
            "handlers": ["console"],
            "propagate": False,
        },
        "django": {
            "handlers": ["console"],
            "level": DJANGO_LOG_LEVEL,
            "propagate": False,
        },
        # Log all unhandled exceptions
        "django.request": {
            "level": LOG_LEVEL,
            "handlers": ["console"],
            "propagate": False,
        },
        "opencensus": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "azure.core.pipeline.policies.http_logging_policy": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}

APPLICATIONINSIGHTS_CONNECTION_STRING = os.getenv(
    "APPLICATIONINSIGHTS_CONNECTION_STRING"
)

if APPLICATIONINSIGHTS_CONNECTION_STRING:
    MIDDLEWARE.append("opencensus.ext.django.middleware.OpencensusMiddleware")

    OPENCENSUS = create_azure_trace_config(
        APPLICATIONINSIGHTS_CONNECTION_STRING, APP_NAME
    )
    LOGGING["handlers"]["azure"] = create_azure_log_handler_config(
        APPLICATIONINSIGHTS_CONNECTION_STRING, APP_NAME
    )
    config_integration.trace_integrations(["logging"])

    LOGGING["root"]["handlers"].append("azure")
    for logger_name, logger_details in LOGGING["loggers"].items():
        LOGGING["loggers"][logger_name]["handlers"].append("azure")


OBJECTSTORE = dict(
    VERSION="2.0",
    AUTHURL="https://identity.stack.cloudvps.com/v2.0",
    TENANT_NAME="BGE000081_BOUWDOSSIERS",
    TENANT_ID="9d078258c1a547c09e0b5f88834554f1",
    USER=os.getenv("OBJECTSTORE_USER", "bouwdossiers"),
    PASSWORD=os.getenv("BOUWDOSSIERS_OBJECTSTORE_PASSWORD"),
    REGION_NAME="NL",
)

BOUWDOSSIERS_OBJECTSTORE_CONTAINER = os.getenv(
    "BOUWDOSSIERS_OBJECTSTORE_CONTAINER", "dossiers_acceptance"
)

STORAGE_ACCOUNT_URL = os.getenv("STORAGE_ACCOUNT_URL")

PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
DATA_DIR = "/tmp/bouwdossiers"

# SWAGGER
SWAG_PATH = "acc.bouwdossiers.amsterdam.nl/iiif-metadata-server/docs"

if DEBUG:
    SWAG_PATH = "127.0.0.1:8000/iiif-metadata-server/docs"

SWAGGER_SETTINGS = {
    "exclude_namespaces": [],
    "api_version": "0.1",
    "api_path": "/",
    "enabled_methods": [
        "get",
    ],
    "api_key": "",
    "USE_SESSION_AUTH": False,
    "VALIDATOR_URL": None,
    "is_authenticated": False,
    "is_superuser": False,
    "unauthenticated_user": "django.contrib.auth.models.AnonymousUser",
    "permission_denied_handler": None,
    "resource_access_handler": None,
    "protocol": "https" if not DEBUG else "",
    "base_path": SWAG_PATH,
    "info": {
        "contact": "atlas.basisinformatie@amsterdam.nl",
        "description": "This is the Bouwdossiers API server.",
        "license": "Not known yet",
        "termsOfServiceUrl": "https://data.amsterdam.nl/terms/",
        "title": "Bouwdossiers",
    },
    "doc_expansion": "list",
}

HEALTH_MODEL = "bouwdossiers.Bouwdossier"


DUMP_DIR = "mks-dump"

TESTING = len(sys.argv) > 1 and sys.argv[1] == "test"

REST_FRAMEWORK = dict(
    PAGE_SIZE=100,
    MAX_PAGINATE_BY=100,
    DEFAULT_PAGINATION_CLASS="rest_framework.pagination.PageNumberPagination",
    UNAUTHENTICATED_USER={},
    UNAUTHENTICATED_TOKEN={},
    DEFAULT_AUTHENTICATION_CLASSES=(
        # 'rest_framework.authentication.BasicAuthentication',
        # 'rest_framework.authentication.SessionAuthentication',
    ),
    DEFAULT_RENDERER_CLASSES=(
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
    DEFAULT_FILTER_BACKENDS=(
        # 'rest_framework.filters.DjangoFilterBackend',
        "django_filters.rest_framework.DjangoFilterBackend",
        # 'rest_framework.filters.OrderingFilter',
    ),
    COERCE_DECIMAL_TO_STRING=True,
)

IIIF_BASE_URL = os.getenv("IIIF_BASE_URL", "https://bouwdossiers.amsterdam.nl/iiif/2/")

DATADIENSTEN_API_BASE_URL = os.getenv(
    "DATADIENSTEN_API_BASE_URL", "https://api.data.amsterdam.nl"
)
BAG_CSV_BASE_URL = os.getenv(
    "BAG_CSV_BASE_URL", "https://amsterdamdadipub.blob.core.windows.net/bulk-data/csv"
)

AZURITE_STORAGE_CONNECTION_STRING = os.getenv("AZURITE_STORAGE_CONNECTION_STRING")

AZURE_CONTAINER_NAME_BAG = "bag"
AZURE_CONTAINER_NAME_DOSSIERS = "dossiers"

MIN_BOUWDOSSIERS_COUNT = os.getenv("MIN_BOUWDOSSIERS_COUNT", 10000)

BAG_DUMP_BASE_URL = os.getenv(
    "BAG_DUMP_BASE_URL", "https://api.data.amsterdam.nl/bulk-data/csv"
)

CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": [SELF],
        "frame-ancestors": [SELF],
        "script-src": [SELF, NONCE],
        "img-src": [SELF, "data:"],
        "style-src": [SELF, NONCE],
        "connect-src": [SELF],
    },
}
