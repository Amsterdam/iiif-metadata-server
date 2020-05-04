import factory

from bouwdossiers import models


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

    source = models.SOURCE_EDEPOT
    importfile = factory.SubFactory(ImportFileFactory)
    dossiernr = '12345'
    stadsdeel = 'AA'
    titel = 'weesperstraat 113 - 117'
    datering = "1998-01-01"
    dossier_status = None
    dossier_type = 'verbouwing'
    access = models.ACCESS_PUBLIC


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
    stadsdeel = 'AA'


class DocumentFactory(factory.DjangoModelFactory):
    class Meta:
        django_get_or_create = ('subdossier_titel',)
        model = models.Document

    bouwdossier = factory.SubFactory(BouwDossierFactory)
    subdossier_titel = 'Tekeningen (plattegrond)'
    bestanden = ['SU10000010_00001.jpg']
    access = models.ACCESS_RESTRICTED
    barcode = 'ST100'
