from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.db.models.functions import Centroid, Transform
from django.contrib.postgres.fields import ArrayField
from django.db import models

from bag.querysets import (
    NummeraanduidingQuerySet,
    PandQuerySet,
    VerblijfsobjectQuerySet,
)


class BagObject:
    def is_verblijfsobject(self):
        return False

    def is_ligplaats(self):
        return False

    def is_standplaats(self):
        return False

    def type_str(self):
        raise NotImplementedError()


class TransformedGeometrieManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(
                transformed_geometrie=Transform(
                    "geometrie", srid=settings.WORLD_GEODETIC_SYSTEM_SRID
                ),
                centroid=Centroid("transformed_geometrie"),
            )
        )


class GeoModel(models.Model):
    transformed_geo_objects = TransformedGeometrieManager()
    objects = models.Manager()

    class Meta:
        abstract = True

class Ligplaats(GeoModel, BagObject):
    id = models.CharField(max_length=16, primary_key=True, db_column="identificatie")
    document_mutatie = models.DateField(db_column="documentdatum")
    document_nummer = models.CharField(max_length=20, db_column="documentnummer")
    begin_geldigheid = models.DateField(db_column="begingeldigheid")
    einde_geldigheid = models.DateField(null=True, db_column="eindgeldigheid")
    indicatie_geconstateerd = models.BooleanField(db_column="geconstateerd")
    geometrie = gis_models.PolygonField(srid=28992)
    status = models.CharField(max_length=80, db_column="statusomschrijving")
    buurt = models.CharField(max_length=16, db_column="ligtinbuurtid", null=True)

    volgnummer = models.IntegerField()
    registratiedatum = models.DateField()
    statuscode = models.CharField(max_length=1)
    heeft_hoofdadres = models.CharField(
        max_length=16, db_column="heefthoofdadresid", null=True
    )
    dossier = models.CharField(max_length=16, db_column="heeftdossierid", null=True)
    proces_code = models.CharField(max_length=4, db_column="bagprocescode", null=True)
    proces_omschrijving = models.CharField(
        max_length=80, db_column="bagprocesomschrijving", null=True
    )

    objects = models.Manager()

    def __str__(self):
        return self.id

    def is_ligplaats(self):
        return True

    def type_str(self):
        return "Ligplaats"

    class Meta:
        db_table = "bag_ligplaats"


class Openbareruimte(GeoModel):
    id = models.CharField(max_length=16, primary_key=True, db_column="identificatie")
    document_mutatie = models.DateField(db_column="documentdatum")
    document_nummer = models.CharField(max_length=20, db_column="documentnummer")
    begin_geldigheid = models.DateField(db_column="begingeldigheid")
    einde_geldigheid = models.DateField(null=True, db_column="eindgeldigheid")
    type = models.CharField(max_length=80, db_column="typeomschrijving")
    naam = models.CharField(max_length=80)
    naam_nen = models.CharField(max_length=80, db_column="naamnen")
    geometrie = gis_models.GeometryField(srid=28992, null=True)
    omschrijving = models.TextField(
        null=True, db_column="beschrijvingnaam"
    )  # Up to 2000 characters
    woonplaats_id = models.CharField(
        max_length=16, db_column="ligtinwoonplaatsid", null=True
    )
    status = models.CharField(max_length=80, db_column="statusomschrijving")

    volgnummer = models.IntegerField()
    registratiedatum = models.DateField()
    straatcode = models.CharField(max_length=16, null=True)
    straatnaam = models.CharField(max_length=80, null=True, db_column="straatnaamptt")
    statuscode = models.CharField(max_length=1)
    geconstateerd = models.BooleanField()
    typecode = models.CharField(max_length=1)
    dossier = models.CharField(max_length=16, db_column="heeftdossierid", null=True)
    proces_code = models.CharField(max_length=4, db_column="bagprocescode", null=True)
    proces_omschrijving = models.CharField(
        max_length=80, db_column="bagprocesomschrijving", null=True
    )

    def __str__(self):
        return self.naam

    class Meta:
        db_table = "bag_openbareruimte"


class Standplaats(GeoModel, BagObject):
    id = models.CharField(max_length=16, primary_key=True, db_column="identificatie")
    document_mutatie = models.DateField(db_column="documentdatum")
    document_nummer = models.CharField(max_length=20, db_column="documentnummer")
    begin_geldigheid = models.DateField(db_column="begingeldigheid")
    einde_geldigheid = models.DateField(null=True, db_column="eindgeldigheid")
    indicatie_geconstateerd = models.BooleanField(db_column="geconstateerd")
    geometrie = gis_models.PolygonField(srid=28992)
    buurt = models.CharField(max_length=16, db_column="ligtinbuurtid", null=True)
    status = models.CharField(max_length=80, db_column="statusomschrijving")

    volgnummer = models.IntegerField()
    registratiedatum = models.DateField()
    statuscode = models.CharField(max_length=1)
    hoofdadres = models.CharField(
        max_length=16, db_column="heefthoofdadresid", null=True
    )
    dossier = models.CharField(max_length=16, db_column="heeftdossierid", null=True)
    proces_code = models.CharField(max_length=4, db_column="bagprocescode", null=True)
    proces_omschrijving = models.CharField(
        max_length=80, db_column="bagprocesomschrijving", null=True
    )

    objects = models.Manager()

    def __str__(self):
        return self.id

    def is_standplaats(self):
        return True

    def type_str(self):
        return "Standplaats"

    class Meta:
        db_table = "bag_standplaats"


class Verblijfsobjectpandrelatie(models.Model):
    id = models.AutoField(primary_key=True)
    pand = models.ForeignKey("bag.Pand", on_delete=models.PROTECT)
    verblijfsobject = models.ForeignKey(
        "bag.Verblijfsobject", blank=True, null=True, on_delete=models.PROTECT
    )

    class Meta:
        db_table = "bag_verblijfsobjectpandrelatie"


class Pand(GeoModel):
    id = models.CharField(max_length=16, primary_key=True, db_column="identificatie")
    document_mutatie = models.DateField(db_column="documentdatum")
    document_nummer = models.CharField(max_length=80, db_column="documentnummer")
    begin_geldigheid = models.DateField(db_column="begingeldigheid")
    einde_geldigheid = models.DateField(null=True, db_column="eindgeldigheid")
    bouwjaar = models.IntegerField(null=True, db_column="oorspronkelijkbouwjaar")
    laagste_bouwlaag = models.IntegerField(null=True, db_column="laagstebouwlaag")
    hoogste_bouwlaag = models.IntegerField(null=True, db_column="hoogstebouwlaag")
    geometrie = gis_models.PolygonField(srid=28992)
    pandnaam = models.CharField(max_length=80, null=True, db_column="naam")
    bouwblok = models.CharField(max_length=16, db_column="ligtinbouwblokid", null=True)

    bouwlagen = models.IntegerField(null=True, db_column="aantalbouwlagen")
    ligging = models.CharField(
        max_length=80, db_column="liggingomschrijving", null=True
    )
    type_woonobject = models.CharField(
        max_length=80, db_column="typewoonobject", null=True
    )
    status = models.CharField(max_length=80, db_column="statusomschrijving")

    volgnummer = models.IntegerField()
    registratiedatum = models.DateField()
    geconstateerd = models.BooleanField()
    statuscode = models.CharField(max_length=3)
    ligging_code = models.CharField(max_length=2, db_column="liggingcode", null=True)
    buurt = models.CharField(max_length=16, db_column="ligtinbuurtid", null=True)

    dossier = models.CharField(max_length=16, db_column="heeftdossierid", null=True)
    proces_code = models.CharField(max_length=4, db_column="bagprocescode", null=True)
    proces_omschrijving = models.CharField(
        max_length=80, db_column="bagprocesomschrijving", null=True
    )

    objects = PandQuerySet.as_manager()

    def is_rijtjeswoning(self):
        try:
            return self.rijtjeshuis is not None
        except Rijtjeshuis.DoesNotExist:
            return False

    def __str__(self):
        return self.id

    class Meta:
        db_table = "bag_pand"


class Verblijfsobject(GeoModel, BagObject):
    id = models.CharField(max_length=16, primary_key=True, db_column="identificatie")
    document_mutatie = models.DateField(db_column="documentdatum")
    document_nummer = models.CharField(max_length=80, db_column="documentnummer")
    begin_geldigheid = models.DateField(db_column="begingeldigheid")
    einde_geldigheid = models.DateField(null=True, db_column="eindgeldigheid")
    oppervlakte = models.IntegerField(null=True)
    verdieping_toegang = models.CharField(
        max_length=80, db_column="verdiepingtoegang", null=True
    )
    aantal_eenheden_complex = models.IntegerField(
        null=True, db_column="aantaleenhedencomplex"
    )
    bouwlagen = models.IntegerField(null=True, db_column="aantalbouwlagen")
    aantal_kamers = models.IntegerField(null=True, db_column="aantalkamers")
    indicatie_geconstateerd = models.BooleanField(db_column="geconstateerd")
    geometrie = gis_models.GeometryField(srid=28992, null=True)
    buurt = models.CharField(max_length=16, db_column="ligtinbuurtid", null=True)
    gebruiksdoel_gezondheidszorgfunctie = models.CharField(
        max_length=80,
        db_column="gebruiksdoelgezondheidszorgfunctieomschrijving",
        null=True,
    )
    gebruiksdoel_woonfunctie = models.CharField(
        max_length=80, db_column="gebruiksdoelwoonfunctieomschrijving", null=True
    )
    hoogste_bouwlaag = models.IntegerField(null=True, db_column="hoogstebouwlaag")
    laagste_bouwlaag = models.IntegerField(null=True, db_column="laagstebouwlaag")
    status = models.CharField(max_length=80, db_column="statusomschrijving", null=True)
    reden_afvoer = models.CharField(
        max_length=80, db_column="redenafvoeromschrijving", null=True
    )
    reden_opvoer = models.CharField(
        max_length=80, db_column="redenopvoeromschrijving", null=True
    )
    eigendomsverhouding = models.CharField(
        max_length=80, db_column="eigendomsverhoudingomschrijving", null=True
    )
    gebruiksdoel = models.CharField(
        max_length=80, db_column="feitelijkgebruikomschrijving", null=True
    )
    panden = models.ManyToManyField(
        Pand, through=Verblijfsobjectpandrelatie, related_name="verblijfsobjecten"
    )

    volgnummer = models.IntegerField()
    registratiedatum = models.DateField()
    cbsnummer = models.CharField(max_length=16, null=True)
    indicatie_woningvoorraad = models.CharField(
        max_length=1, db_column="indicatiewoningvoorraad", null=True
    )
    financierings_code = models.CharField(
        max_length=4, db_column="financieringscodecode", null=True
    )
    financierings_omschrijving = models.CharField(
        max_length=80, db_column="financieringscodeomschrijving", null=True
    )
    hoofdadres = models.CharField(
        max_length=16, db_column="heefthoofdadresid", null=True
    )
    status_code = models.IntegerField(db_column="statuscode", null=True)
    gebruiksdoel_woonfunctie_code = models.CharField(
        max_length=4, db_column="gebruiksdoelwoonfunctiecode", null=True
    )
    gebruiksdoel_gezondheidszorgfunctie_code = models.CharField(
        max_length=4, db_column="gebruiksdoelgezondheidszorgfunctiecode", null=True
    )
    eigendomsverhouding_code = models.CharField(
        max_length=4, db_column="eigendomsverhoudingcode", null=True
    )
    feitelijk_gebruik_code = models.CharField(
        max_length=4, db_column="feitelijkgebruikcode", null=True
    )
    reden_opvoer_code = models.CharField(
        max_length=4, db_column="redenopvoercode", null=True
    )
    reden_afvoer_code = models.CharField(
        max_length=4, db_column="redenafvoercode", null=True
    )
    dossier = models.CharField(max_length=16, db_column="heeftdossierid", null=True)
    proces_code = models.CharField(max_length=4, db_column="bagprocescode", null=True)
    proces_omschrijving = models.CharField(
        max_length=80, db_column="bagprocesomschrijving", null=True
    )

    objects = VerblijfsobjectQuerySet.as_manager()

    def __str__(self):
        return self.id

    def is_verblijfsobject(self):
        return True

    def type_str(self):
        return "Verblijfsobject"

    class Meta:
        db_table = "bag_verblijfsobject"


class Nummeraanduiding(models.Model):
    id = models.CharField(max_length=16, primary_key=True, db_column="identificatie")
    document_mutatie = models.DateField(db_column="documentdatum")
    document_nummer = models.CharField(max_length=40, db_column="documentnummer")
    begin_geldigheid = models.DateTimeField(db_column="begingeldigheid")
    eind_geldigheid = models.DateTimeField(null=True, db_column="eindgeldigheid")
    huisnummer = models.IntegerField()
    huisletter = models.CharField(max_length=1, null=True)
    huisnummer_toevoeging = models.CharField(
        max_length=4, null=True, db_column="huisnummertoevoeging"
    )
    postcode = models.CharField(max_length=6, null=True)
    ligplaats = models.ForeignKey(
        Ligplaats,
        null=True,
        db_column="adresseertligplaatsid",
        on_delete=models.CASCADE,
        related_name="nummeraanduidingen",
    )
    openbare_ruimte = models.ForeignKey(
        Openbareruimte,
        null=True,
        db_column="ligtaanopenbareruimteid",
        on_delete=models.CASCADE,
        related_name="nummeraanduidingen",
    )
    standplaats = models.ForeignKey(
        Standplaats,
        null=True,
        db_column="adresseertstandplaatsid",
        on_delete=models.CASCADE,
        related_name="nummeraanduidingen",
    )
    verblijfsobject = models.ForeignKey(
        Verblijfsobject,
        null=True,
        db_column="adresseertverblijfsobjectid",
        on_delete=models.CASCADE,
        related_name="nummeraanduidingen",
    )
    type_adres = models.CharField(max_length=80, db_column="typeadres", null=True)
    status = models.CharField(max_length=80, db_column="statusomschrijving", null=True)

    volgnummer = models.IntegerField()
    registratiedatum = models.DateTimeField()
    geconstateerd = models.BooleanField()
    woonplaats = models.CharField(
        max_length=80, db_column="ligtinwoonplaatsid", null=True
    )
    type_adresseerbaar_object_code = models.CharField(
        max_length=4, db_column="typeadresseerbaarobjectcode", null=True
    )
    type_adresseerbaar_object_omschrijving = models.CharField(
        max_length=80, db_column="typeadresseerbaarobjectomschrijving", null=True
    )
    status_code = models.CharField(max_length=4, db_column="statuscode", null=True)
    dossier = models.CharField(max_length=40, db_column="heeftdossierid", null=True)
    proces_code = models.CharField(max_length=4, db_column="bagprocescode", null=True)
    proces_omschrijving = models.CharField(
        max_length=80, db_column="bagprocesomschrijving", null=True
    )

    objects = NummeraanduidingQuerySet.as_manager()

    def __str__(self):
        huisnr_toevoeging = (
            f"-{self.huisnummer_toevoeging}" if self.huisnummer_toevoeging else ""
        )
        huisletter = self.huisletter if self.huisletter else ""
        return f"{self.openbare_ruimte} {self.huisnummer}{huisletter}{huisnr_toevoeging} ({self.type_adres})"

    class Meta:
        db_table = "bag_nummeraanduiding"