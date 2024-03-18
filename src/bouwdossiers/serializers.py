import logging
import re

from datapunt_api.serializers import DisplayField, HALSerializer, LinksField
from django.conf import settings
from rest_framework.reverse import reverse
from rest_framework.serializers import ModelSerializer

from importer.models import (
    SOURCE_CHOICES,
    SOURCE_EDEPOT,
    SOURCE_WABO,
    Adres,
    BouwDossier,
    Document,
)

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
        """
        result = super().to_representation(instance)
        _bestanden = []

        for bestand in result["bestanden"]:
            filename = bestand.replace(" ", "%20")
            if instance.bouwdossier.source == SOURCE_EDEPOT:
                filename = filename.replace("/", "-")
                # If stadsdeel en dossiernr are not part of the filename, they  will be added to the beginning of the filename in the form of
                # SD12345. In this way iiif-auth-proxy can determine the access for this bestand in de the dossier.
                m = re.search(r"^([A-Z]+)-(\d+)-", filename)
                if (
                    m
                    and m.group(1) == instance.bouwdossier.stadsdeel
                    and int(m.group(2)) == instance.bouwdossier.dossiernr
                ):
                    url = f"{settings.IIIF_BASE_URL}{dict(SOURCE_CHOICES)[instance.bouwdossier.source]}:{filename}"
                else:
                    url = f"{settings.IIIF_BASE_URL}{dict(SOURCE_CHOICES)[instance.bouwdossier.source]}:{instance.bouwdossier.stadsdeel}{instance.bouwdossier.dossiernr}-{filename}"

            elif instance.bouwdossier.source == SOURCE_WABO:
                file_reference = f"{instance.bouwdossier.stadsdeel}-{instance.bouwdossier.dossiernr}-{instance.bouwdossier.olo_liaan_nummer}_{instance.barcode}"
                url = f"{settings.IIIF_BASE_URL}{dict(SOURCE_CHOICES)[instance.bouwdossier.source]}:{file_reference}"

            _bestanden.append({"filename": filename, "url": url})

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

        url_kwargs = {"pk": obj.stadsdeel + str(obj.dossiernr)}

        return reverse(view_name, kwargs=url_kwargs, request=request, format=_format)


class CustomHalSerializer(HALSerializer):
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
