import logging

from datapunt_api.serializers import HALSerializer, DisplayField, LinksField
from rest_framework.serializers import ModelSerializer
from rest_framework.reverse import reverse

from stadsarchief.datasets.bouwdossiers.models import BouwDossier, SubDossier, Adres

log = logging.getLogger(__name__)


class AdresSerializer(ModelSerializer):
    class Meta:
        model = Adres
        fields = ('straat', 'huisnummer_van', 'huisnummer_tot', 'nummeraanduidingen', 'nummeraanduidingen_label',
                  'panden', 'verblijfsobjecten', 'verblijfsobjecten_label')


class SubDossierSerializer(ModelSerializer):
    class Meta:
        model = SubDossier
        fields = ('titel',  'bestanden', )


class CustomLinksField(LinksField):

    def get_url(self, obj, view_name, request, _format):

        url_kwargs = {
            'pk': obj.stadsdeel + str(obj.dossiernr)
        }

        return reverse(
            view_name, kwargs=url_kwargs, request=request, format=_format)


class CustomHalSerializer(HALSerializer):
    serializer_url_field = CustomLinksField


class BouwDossierSerializer(CustomHalSerializer):
    subdossiers = SubDossierSerializer(many=True)
    adressen = AdresSerializer(many=True)
    _display = DisplayField()

    class Meta:
        model = BouwDossier
        fields = (
            '_links',
            'id',
            'titel',
            '_display',
            'dossiernr',
            'stadsdeel',
            'datering',
            'dossier_type',
            'dossier_status',
            'subdossiers',
            'adressen',
        )
