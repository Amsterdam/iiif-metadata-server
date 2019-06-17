import factory

from stadsarchief.datasets.bouwdossiers import models


class ImportFileFactory(factory.DjangoModelFactory):
    class Meta:
        django_get_or_create = ('name',)
        model = models.ImportFile

    name = 'test.xml'
    status = models.IMPORT_FINISHED
    last_import = "2019-04-12 13:38:23"


class BouwDossierFactory(factory.DjangoModelFactory):
    class Meta:
        django_get_or_create = ('dossiernr', 'stadsdeel')
        model = models.BouwDossier

    importfile = factory.SubFactory(ImportFileFactory)
    dossiernr = '12345'
    stadsdeel = 'A'
    titel = 'weesperstraat 113 - 117'
    datering = "1998-01-01"
    dossier_status = None
    dossier_type = 'verbouwing'
    access = models.ACCESS_RESTRICTED


class AdresFactory(factory.DjangoModelFactory):
    class Meta:
        django_get_or_create = ('straat', 'huisnummer_van')
        model = models.Adres

    bouwdossier = factory.SubFactory(BouwDossierFactory)
    straat = 'weesperstraat'
    huisnummer_van = 113
    huisnummer_tot = 117
    openbareruimte_id = '0363300000004835'
    nummeraanduidingen = ['0363200000406187']
    nummeraanduidingen_label = ['Weesperstraat 113']
    panden = ['0363100012165490']
    verblijfsobjecten = ['036301000xxxxxxx']
    verblijfsobjecten_label = ['Weesperstraat 113']
    stadsdeel = 'A'


class SubDossierFactory(factory.DjangoModelFactory):
    class Meta:
        django_get_or_create = ('titel',)
        model = models.SubDossier

    bouwdossier = factory.SubFactory(BouwDossierFactory)
    titel = 'Tekeningen (plattegrond)'
    bestanden = ['SU10000010_00001.jpg']
    access = models.ACCESS_RESTRICTED
