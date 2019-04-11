import logging

from django_filters.rest_framework import filters
from django_filters.rest_framework import FilterSet
from datapunt_api.rest import DatapuntViewSet

from stadsarchief.datasets.bouwdossiers import serializers, models

log = logging.getLogger(__name__)


class BouwDossierFilter(FilterSet):
    nummeraanduiding = filters.CharFilter(field_name='adressen__nummeraanduidingen__landelijk_id')
    pand = filters.CharFilter(field_name='adressen__panden__landelijk_id')
    openbareruimte = filters.CharFilter(field_name='adressen__openbareruimte_id')
    min_datering = filters.CharFilter(field_name='datering__year', lookup_expr='gte')
    max_datering = filters.CharFilter(field_name='datering__year', lookup_expr='lte')
    subdossier = filters.CharFilter(field_name='subdossiers__titel', lookup_expr='istartswith')
    dossiernr = filters.CharFilter()
    stadsdeel = filters.CharFilter()
    dossier_type = filters.CharFilter()

    class Meta:
        model = models.BouwDossier

        fields = (
            'dossiernr',
            'stadsdeel',
            'nummeraanduiding',
            'pand',
            'openbareruimte',
            'min_datering',
            'max_datering',
            'subdossier'
        )

    # ordering = ('naam',)


class BouwDossierViewSet(DatapuntViewSet):
    filter_class = BouwDossierFilter

    queryset = (
        models.BouwDossier.objects.all()
        .prefetch_related('adressen')
        .prefetch_related('subdossiers')
        .prefetch_related('adressen__nummeraanduidingen')
        .prefetch_related('adressen__panden')
    )

    def get_serializer_class(self):
        return serializers.BouwDossierSerializer
