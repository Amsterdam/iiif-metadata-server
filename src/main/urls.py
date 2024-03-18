from django.conf import settings
from django.conf.urls import include
from django.urls import re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from bouwdossiers import urls as bouwdossiers_urls

grouped_url_patterns = {
    "base_patterns": [
        re_path(r"^status/", include("health.urls")),
    ],
    "bouwdossiers_patterns": [
        re_path(r"^iiif-metadata/", include(bouwdossiers_urls.urls)),
    ],
}

schema_view = get_schema_view(
    openapi.Info(
        title="Bouwdossiers API",
        default_version="v1",
        description="Bouwdossiers API",
        terms_of_service="https://data.amsterdam.nl/",
        contact=openapi.Contact(email="datapunt@amsterdam.nl"),
        license=openapi.License(name="CC0 1.0 Universal"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    re_path(
        r"^iiif-metadata/docs/swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=None),
        name="schema-json",
    ),
    re_path(
        r"^iiif-metadata/docs/swagger/$",
        schema_view.with_ui("swagger", cache_timeout=None),
        name="schema-swagger-ui",
    ),
    re_path(
        r"^iiif-metadata/docs/redoc/$",
        schema_view.with_ui("redoc", cache_timeout=None),
        name="schema-redoc",
    ),
]

urlpatterns += [
    url for pattern_list in grouped_url_patterns.values() for url in pattern_list
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns.extend(
        [
            re_path(r"^__debug__/", include(debug_toolbar.urls)),
        ]
    )
