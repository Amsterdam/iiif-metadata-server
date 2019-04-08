import logging

from datapunt_api.rest import DatapuntViewSet

# from django.contrib.gis.db.models.functions import Distance
# from django.contrib.gis.geos import Point
# from django.contrib.gis.measure import D
# from django_filters.rest_framework import FilterSet
# from django_filters.rest_framework import filters
# from rest_framework import serializers as rest_serializers
# from rest_framework import response
from django_filters.rest_framework import DjangoFilterBackend

from stadsarchief.datasets.bouwdossiers import serializers, models

log = logging.getLogger(__name__)


class BouwDossierViewSet(DatapuntViewSet):
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('dossiernr', 'stadsdeel')

    queryset = (
        models.BouwDossier.objects.all()
            .prefetch_related('adressen')
            .prefetch_related('subdossiers')
            .prefetch_related('subdossiers__bestanden')
            .prefetch_related('adressen__nummeraanduidingen')
            .prefetch_related('adressen__panden')
    )

    def get_serializer_class(self):
        return serializers.BouwDossierSerializer

