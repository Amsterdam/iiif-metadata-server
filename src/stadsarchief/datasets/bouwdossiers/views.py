import logging

from django_filters.rest_framework import filters
from django_filters.rest_framework import FilterSet
from django.shortcuts import get_object_or_404
# from django.db.models import Prefetch
from datapunt_api.rest import DatapuntViewSet

from stadsarchief.datasets.bouwdossiers import serializers, models

log = logging.getLogger(__name__)


class BouwDossierFilter(FilterSet):
    nummeraanduiding = filters.CharFilter(field_name='adressen__nummeraanduidingen', method='array_contains_filter')
    pand = filters.CharFilter(field_name='adressen__panden', method='array_contains_filter')
    verblijfsobject = filters.CharFilter(field_name='adressen__verblijfsobjecten', method='array_contains_filter')
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
            'verblijfsobject',
            'pand',
            'openbareruimte',
            'min_datering',
            'max_datering',
            'subdossier'
        )

    def array_contains_filter(self, queryset, _filter_name, value):
        if not isinstance(value, list):
            value = [value]
        lookup = '%s__%s' % (_filter_name, 'contains')
        return queryset.filter(**{lookup: value})


class BouwDossierViewSet(DatapuntViewSet):
    filter_class = BouwDossierFilter

    queryset = (
        models.BouwDossier.objects.all().filter(access='X')
        .prefetch_related('adressen')
        .prefetch_related('subdossiers')
        #     Prefetch('subdossiers', queryset=models.SubDossier.objects.filter(access='P'))
        # )
    )

    def get_serializer_class(self):
        return serializers.BouwDossierSerializer

    def get_object(self):
        pk = self.kwargs['pk']
        first = pk[0]
        if pk and first.isalpha():
            stadsdeel = first
            dossiernr = pk[1:]
            obj = get_object_or_404(models.BouwDossier, stadsdeel=stadsdeel, dossiernr=dossiernr)
        else:
            obj = get_object_or_404(models.BouwDossier, pk=pk)

        return obj
