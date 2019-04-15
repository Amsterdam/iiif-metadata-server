import logging

from datapunt_api.serializers import HALSerializer, DisplayField
from rest_framework.serializers import ModelSerializer

from stadsarchief.datasets.bouwdossiers.models import BouwDossier, SubDossier, Adres, Pand, Nummeraanduiding

log = logging.getLogger(__name__)


class PandSerializer(ModelSerializer):
    class Meta:
        model = Pand
        fields = ('landelijk_id',)


class NummeraanduidingSerializer(ModelSerializer):
    class Meta:
        model = Nummeraanduiding
        fields = ('landelijk_id',)


class AdresSerializer(ModelSerializer):
    nummeraanduidingen = NummeraanduidingSerializer(many=True)
    panden = PandSerializer(many=True)

    class Meta:
        model = Adres
        fields = ('straat', 'huisnummer_van', 'huisnummer_tot', 'nummeraanduidingen', 'panden')


class SubDossierSerializer(ModelSerializer):
    class Meta:
        model = SubDossier
        fields = ('titel',  'bestanden', )


class BouwDossierSerializer(HALSerializer):
    subdossiers = SubDossierSerializer(many=True)
    adressen = AdresSerializer(many=True)
    _display = DisplayField()

    class Meta:
        model = BouwDossier
        fields = (
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
