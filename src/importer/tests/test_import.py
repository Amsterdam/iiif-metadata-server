from django.conf import settings
from django.db import connection
from django.test import TestCase

from importer import batch, models


class APITest(TestCase):
    @classmethod
    def setUpTestData(cls):
        with open('importer/tests/data/add_bag.sql') as fbag:
            bag_data = fbag.read()
        with connection.cursor() as cursor:
            cursor.execute(bag_data)

    def setUp(self):
        settings.DATA_DIR = 'importer/tests/data'

    def test_prewabo_import(self):
        batch.import_pre_wabo_dossiers()
        batch.add_bag_ids_to_pre_wabo()

        bd3 = models.BouwDossier.objects.get(dossiernr=3)
        self.assertEqual(bd3.stadsdeel, 'SA')
        self.assertEqual(bd3.titel, "Hoogte Kadijk 40")
        self.assertEqual(bd3.datering.strftime("%Y"), "2003")
        self.assertEqual(bd3.dossier_type, "verbouwing")
        self.assertEqual(bd3.access, "PUBLIC")
        self.assertEqual(bd3.source, "EDEPOT")

        bd3_addressen = models.Adres.objects.filter(bouwdossier_id=bd3.id)
        adres0 = bd3_addressen.first()
        self.assertEqual(adres0.straat, "Hoogte Kadijk")
        self.assertEqual(adres0.huisnummer_van, 40)
        self.assertEqual(adres0.huisnummer_tot, 40)

        bd3_documenten = models.Document.objects.filter(bouwdossier_id=bd3.id).order_by('id').all()
        document0 = bd3_documenten.first()
        self.assertEqual(document0.barcode, "SA00000007")
        self.assertEqual(document0.subdossier_titel, "Aanvraag en behandeling")
        self.assertEqual(document0.bestanden, [
            "SA/00003/SA00000007_00001.jpg",
            "SA/00003/SA00000007_00002.jpg",
            "SA/00003/SA00000007_00003.jpg"
        ])
        self.assertEqual(document0.access, "PUBLIC")

        bd123 = models.BouwDossier.objects.get(dossiernr=123)
        bd123_documenten = models.Document.objects.filter(bouwdossier_id=bd123.id).order_by('id').all()
        for document123 in bd123_documenten.all():
            if document123.barcode == "SA00001038":
                self.assertEqual(document123.access, "RESTRICTED")
            elif document123.barcode == "SA00001039":
                self.assertEqual(document123.access, "PUBLIC")

        bd21388 = models.BouwDossier.objects.get(dossiernr=21388)
        bd21388_addressen = models.Adres.objects.filter(bouwdossier_id=bd21388.id)
        fdb = bd21388_addressen.get(straat='Feike de Boerlaan')
        # 0363010000959579 Feike de Boerlaan 29
        self.assertTrue('0363010000959579' in fdb.verblijfsobjecten)
        # 0363010000998545 Feike de Boerlaan 14
        self.assertFalse('0363010000998545' in fdb.verblijfsobjecten)
        # 0363200000461980 Feike de Boerlaan 83 nummeraanduiding
        self.assertTrue('0363200000461980' in fdb.nummeraanduidingen)
        # 0363200000470955 Feike de Boerlaan 290 nummeraanduiding
        self.assertFalse('0363200000470955' in fdb.nummeraanduidingen)

    def test_wabo_import(self):
        batch.import_wabo_dossiers()

        bd1 = models.BouwDossier.objects.get(dossiernr=189)
        self.assertEqual(bd1.stadsdeel, 'SDC')
        self.assertEqual(bd1.titel, "het herstellen van de fundering en het veranderen en vernieuwen van de rechterzijvleugel van het gebouwencomplex Lauriergracht 1161 met bestemming daarvan tot kantoor")
        self.assertEqual(bd1.datering.strftime("%Y"), "2010")
        self.assertEqual(bd1.dossier_type, "omgevingsvergunning")
        self.assertEqual(bd1.access, "PUBLIC")
        self.assertEqual(bd1.source, "WABO")
        self.assertEqual(bd1.olo_liaan_nummer, 189)
        self.assertEqual(bd1.wabo_bron, "KEY2")

        bd1_addressen = models.Adres.objects.filter(bouwdossier_id=bd1.id)
        self.assertEqual(bd1_addressen.count(), 25)

        adres1 = bd1_addressen.first()
        self.assertEqual(adres1.straat, "Lauriergracht")
        self.assertEqual(adres1.huisnummer_van, 1161)
        self.assertEqual(adres1.huisnummer_toevoeging, "H")
        self.assertEqual(adres1.huisnummer_tot, None)
        self.assertEqual(adres1.openbareruimte_id, "0363300000004136")
        self.assertEqual(adres1.verblijfsobjecten, ['0363010000719556'])
        self.assertEqual(adres1.panden, ['0363100012168986'])

        bd1_documenten = models.Document.objects.filter(bouwdossier_id=bd1.id).order_by('id').all()
        self.assertEqual(len(bd1_documenten), 20)
        document5 = bd1_documenten[5]
        self.assertEqual(document5.document_omschrijving, "Bij besluit behorende gewaarmerkte bescheiden - vergunningset189_bijlage16.pdf | Bij besluit behorende gewaarmerkte bescheiden: vergunningset")
        self.assertEqual(document5.bestanden, ['SDC/KEY2Vergunning_33/Documentum/0901b69980335dcb.pdf'])
        self.assertEqual(document5.oorspronkelijk_pad, ['G:\\Export files\\documentum\\primary/25/0901b69980335dcb'])
        self.assertEqual(document5.access, models.ACCESS_PUBLIC)

        document6 = bd1_documenten[6]
        self.assertEqual(document6.document_omschrijving, "Bij besluit behorende gewaarmerkte bescheiden - vergunningset189_bijlage01.pdf | Bij besluit behorende gewaarmerkte bescheiden: vergunningset")
        self.assertEqual(document6.bestanden, ['SDC/KEY2Vergunning_33/Documentum/0901b69980335dcd.pdf'])
        self.assertEqual(document6.oorspronkelijk_pad, ['G:\\Export files\\documentum\\primary/25/0901b69980335dcd'])
        self.assertEqual(document6.access, models.ACCESS_RESTRICTED)

        # Test whether the dossier and document with no accesibility keys are set to restricted
        bd2 = models.BouwDossier.objects.get(dossiernr=233)
        self.assertEqual(bd2.access, models.ACCESS_RESTRICTED)

        bd2_documenten = models.Document.objects.filter(bouwdossier_id=bd2.id).order_by('id').all()
        document1 = bd2_documenten[0]
        self.assertEqual(document1.access, models.ACCESS_RESTRICTED)

        batch.add_bag_ids_to_wabo()
        # test import bag ids

    def validate_import(self):
        batch.import_pre_wabo_dossiers()
        batch.add_bag_ids_to_pre_wabo()
        batch.import_wabo_dossiers()
        batch.add_bag_ids_to_wabo()
        batch.validate_import(min_bouwdossiers_count=38)

