import logging

from datapunt_api.serializers import HALSerializer, DisplayField
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from bouwdossiers.models import Bouwdossier

log = logging.getLogger(__name__)


class BowdossierSerializer(HALSerializer):
    _display = DisplayField()

    class Meta:
        model = Bouwdossier
        fields = (
            'titel',
            '_display',
        )
