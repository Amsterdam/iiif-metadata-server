import logging

from datapunt_api.rest import DatapuntViewSet

# from django.contrib.gis.db.models.functions import Distance
# from django.contrib.gis.geos import Point
# from django.contrib.gis.measure import D
# from django_filters.rest_framework import FilterSet
# from django_filters.rest_framework import filters
# from rest_framework import serializers as rest_serializers
# from rest_framework import response

from stadsarchief.datasets.bouwdossiers import serializers
from stadsarchief import models

log = logging.getLogger(__name__)


class BouwdossierViewSet(DatapuntViewSet):
    queryset = (
        models.Bouwdossier.objects.all()
            .prefetch_related('adres')
            .prefetch_related('subdossier')
            .prefetch_related('subdossier__bestand')
            .prefetch_related('adres__nummeraanduiding')
            .prefetch_related('adres__pand')
    )

    def get_serializer_class(self):
        return serializers.BowdossierSerializer

