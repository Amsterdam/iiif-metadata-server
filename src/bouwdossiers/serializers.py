import logging
import re

from django.conf import settings
from rest_framework.reverse import reverse
from rest_framework.serializers import HyperlinkedModelSerializer, ModelSerializer

from importer.models import (
    SOURCE_CHOICES,
    Adres,
    BouwDossier,
    Document,
)
from main.drf import DisplayField, LinksField

log = logging.getLogger(__name__)


class AdresSerializer(ModelSerializer):
    class Meta:
        model = Adres
        fields = (
            "straat",
            "huisnummer_van",
            "huisnummer_tot",
            "nummeraanduidingen",
            "nummeraanduidingen_label",
            "panden",
            "verblijfsobjecten",
            "verblijfsobjecten_label",
            "openbareruimte_id",
            "huisnummer_letter",
            "huisnummer_toevoeging",
            "locatie_aanduiding",
        )


class DocumentSerializer(ModelSerializer):
    def to_representation(self, instance):
        """
        All bestanden should now be formatted with '-' instead of '/'.
        This decision was made because the iiif-auth-proxy requires the
        use of '-' when retrieving the image and this api is the source
        of the image titles

        The way iiif-auth-proxy can determine the different components of the url:
         - stadsdeel, dossiernr separated by '_': example SD_T-12345
         than ~ for: document_barcode separated by '_'


        """
        result = super().to_representation(instance)
        _bestanden = []

        for index, bestand in enumerate(result["bestanden"]):
            stadsdeel_dossiernr = (
                f"{instance.bouwdossier.stadsdeel}_{instance.bouwdossier.dossiernr}"
            )
            f = re.search(r"\/([^\/]+)$", bestand)
            filename = f.group(1) if f else bestand
            filenr = index
            file_reference = f"{stadsdeel_dossiernr}~{instance.barcode}_{filenr}"
            url = f"{settings.IIIF_BASE_URL}{dict(SOURCE_CHOICES)[instance.bouwdossier.source]}:{file_reference}"

            _bestanden.append({"filename": filename, "file_pad": bestand, "url": url})

        result["bestanden"] = _bestanden

        return result

    class Meta:
        model = Document
        fields = (
            "subdossier_titel",
            "barcode",
            "bestanden",
            "oorspronkelijk_pad",
            "document_omschrijving",
            "access",
            "access_restricted_until",
            "copyright",
            "copyright_until",
            "copyright_holders",
            "copyright_manufacturers",
        )


class CustomLinksField(LinksField):

    def get_url(self, obj, view_name, request, _format):

        url_kwargs = {"pk": obj.stadsdeel + "_" + obj.dossiernr}

        return reverse(view_name, kwargs=url_kwargs, request=request, format=_format)


class CustomHalSerializer(HyperlinkedModelSerializer):
    url_field_name: str = "_links"
    serializer_url_field = CustomLinksField


class BouwDossierSerializer(CustomHalSerializer):
    documenten = DocumentSerializer(many=True)
    adressen = AdresSerializer(many=True)
    _display = DisplayField()

    class Meta:
        model = BouwDossier
        fields = (
            "_links",
            "titel",
            "_display",
            "dossiernr",
            "stadsdeel",
            "datering",
            "dossier_type",
            "gebruiksdoel",
            "bwt_nummer",
            "dossier_status",
            "olo_liaan_nummer",
            "access",
            "access_restricted_until",
            "activiteiten",
            "documenten",
            "adressen",
            "source",
        )
