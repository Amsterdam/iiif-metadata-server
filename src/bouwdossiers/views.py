import logging

from datapunt_api.rest import DatapuntViewSet
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import FilterSet, filters

from bouwdossiers import models, serializers, tools

log = logging.getLogger(__name__)


class BouwDossierFilter(FilterSet):
    nummeraanduiding = filters.CharFilter(field_name='adressen__nummeraanduidingen', method='array_contains_filter')
    pand = filters.CharFilter(field_name='adressen__panden', method='array_contains_filter')
    verblijfsobject = filters.CharFilter(field_name='adressen__verblijfsobjecten', method='array_contains_filter')
    openbareruimte = filters.CharFilter(field_name='adressen__openbareruimte_id')
    min_datering = filters.CharFilter(field_name='datering__year', lookup_expr='gte')
    max_datering = filters.CharFilter(field_name='datering__year', lookup_expr='lte')
    subdossier = filters.CharFilter(field_name='documenten__subdossier_titel', lookup_expr='istartswith')
    dossiernr = filters.NumberFilter()
    dossier = filters.CharFilter(method='dossier_with_stadsdeel')
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
            'subdossier',
            'olo_liaan_nummer',
        )

    def dossier_with_stadsdeel(self, queryset, _filter_name, value):
        stadsdeel, dossiernr = tools.separate_dossier(value)
        return queryset.filter(stadsdeel=stadsdeel, dossiernr=dossiernr)

    def array_contains_filter(self, queryset, _filter_name, value):
        if not isinstance(value, list):
            value = [value]
        lookup = '%s__%s' % (_filter_name, 'contains')
        return queryset.filter(**{lookup: value}).distinct()


class BouwDossierViewSet(DatapuntViewSet):
    filter_class = BouwDossierFilter

    queryset = (
        models.BouwDossier.objects.all()
        .prefetch_related('adressen')
        .prefetch_related('documenten')
    )

    def get_serializer_class(self):
        return serializers.BouwDossierSerializer

    def get_object(self):
        # We expect a key of the form AA0000123 in which AA is the code for the
        # stadsdeel and the numberic part (which can vary in length) is the dossiernumber
        stadsdeel, dossiernr = tools.separate_dossier(self.kwargs['pk'])
        obj = get_object_or_404(self.queryset, stadsdeel=stadsdeel.upper(), dossiernr=dossiernr)

        return obj
