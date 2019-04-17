from django.conf import settings
from django.conf.urls import url, include
from rest_framework import permissions

from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from stadsarchief.datasets.bouwdossiers import urls as bouwdossiers_urls

grouped_url_patterns = {
    'base_patterns': [
        url(r'^status/', include('stadsarchief.health.urls')),
    ],
    'bouwdossiers_patterns': [
        url(r'^stadsarchief/', include(bouwdossiers_urls.urls)),
    ],
}

schema_view = get_schema_view(
    openapi.Info(
        title="Bouwdossiers API",
        default_version='v1',
        description="Bouwdossiers API",
        terms_of_service="https://data.amsterdam.nl/",
        contact=openapi.Contact(email="datapunt@amsterdam.nl"),
        license=openapi.License(name="CC0 1.0 Universal"),
    ),
    public=False,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [url(r'^stadsarchief/docs/swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=None),
                   name='schema-json'),
               url(r'^stadsarchief/docs/swagger/$', schema_view.with_ui('swagger', cache_timeout=None),
                   name='schema-swagger-ui'),
               url(r'^stadsarchief/docs/redoc/$', schema_view.with_ui('redoc', cache_timeout=None),
                   name='schema-redoc'),
               ] + [url for pattern_list in grouped_url_patterns.values()
                    for url in pattern_list]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns.extend([
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ])
