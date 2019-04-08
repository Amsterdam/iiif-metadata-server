import factory

from stadsarchief.datasets.bouwdossiers import models


class BouwDossierFactory(factory.DjangoModelFactory):
    class Meta:
        django_get_or_create = ('dossiernr','stadsdeel')
        model = models.BouwDossier

    id = 1
    dossiernr = '12345'
    stadsdeel = 'A'
    titel = 'weesperstraat 113 - 117'
    datering = '1998'
    dossier_status = None
    dossier_type = 'verbouwing'
    access = models.ACCESS_RESTRICTED


class AdresFactory(factory.DjangoModelFactory):
    class Meta:
        django_get_or_create = ('straat', 'huisnummer_van')
        model = models.Adres

    id = 2
    bouwdossier = factory.SubFactory(BouwDossierFactory)
    straat = 'weesperstraat'
    huisnummer_van = 113
    huisnummer_tot = 117
    _openbareruimte ='weesperstraat'
    _stadsdeel = 'A'


class SubDossierFactory(factory.DjangoModelFactory):
    class Meta:
        django_get_or_create = ('titel',)
        model = models.SubDossier

    id = 3
    bouwdossier = factory.SubFactory(BouwDossierFactory)
    titel = 'Tekeningen (plattegrond)'
    access = models.ACCESS_RESTRICTED


class BestandFactory(factory.DjangoModelFactory):
    class Meta:
        django_get_or_create = ('name',)
        model = models.Bestand

    id = 4
    dossier = factory.SubFactory(BouwDossierFactory)
    subdossier = factory.SubFactory(SubDossierFactory)
    name = 'SU10000010_00001.jpg'
    access = models.ACCESS_RESTRICTED


class NummeraanduidingFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Nummeraanduiding

    id = 5
    adres = factory.SubFactory(AdresFactory)
    landelijk_id = '0363200000406187'


class PandFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Pand

    id = 6
    adres = factory.SubFactory(AdresFactory)
    landelijk_id = '0363100012165490'
