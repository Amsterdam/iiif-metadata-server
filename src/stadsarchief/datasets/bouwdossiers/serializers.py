import logging

from django.conf import settings
from datapunt_api.serializers import HALSerializer, DisplayField, LinksField
from rest_framework.serializers import ModelSerializer
from rest_framework.reverse import reverse

from stadsarchief.datasets.bouwdossiers.models import BouwDossier, Document, Adres, SOURCE_CHOICES

log = logging.getLogger(__name__)


class AdresSerializer(ModelSerializer):
    class Meta:
        model = Adres
        fields = ('straat', 'huisnummer_van', 'huisnummer_tot', 'nummeraanduidingen', 'nummeraanduidingen_label',
                  'panden', 'verblijfsobjecten', 'verblijfsobjecten_label', 'openbareruimte_id')


class DocumentSerializer(ModelSerializer):
    def to_representation(self, instance):
        """
        All bestanden should now be formatted with '-' instead of '/'.
        This decision was made because the iiif-auth-proxy requires the
        use of '-' when retrieving the image and this api is the source
        of the image titles
        """
        result = super().to_representation(instance)
        _bestanden = []

        for bestand in result['bestanden']:
            filename = bestand.replace('/', '-')
            _bestanden.append(
                {
                    'filename': filename,
                    'url': f"{settings.IIIF_BASE_URL}{dict(SOURCE_CHOICES)[instance.bouwdossier.source]}:{filename}"
                }
            )

        result['bestanden'] = _bestanden
        return result

    class Meta:
        model = Document
        fields = ('subdossier_titel',  'barcode', 'bestanden', 'access')


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
    documenten = DocumentSerializer(many=True)
    adressen = AdresSerializer(many=True)
    _display = DisplayField()

    class Meta:
        model = BouwDossier
        fields = (
            '_links',
            'titel',
            '_display',
            'dossiernr',
            'stadsdeel',
            'datering',
            'dossier_type',
            'dossier_status',
            'documenten',
            'adressen',
            'access'
        )
