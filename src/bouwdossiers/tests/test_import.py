from django.conf import settings
from django.test import TransactionTestCase

from bouwdossiers import batch, models


class APITest(TransactionTestCase):
    def setUp(self):
        settings.DATA_DIR = 'bouwdossiers/tests/data'

    def test_prewabo_import(self):
        batch.import_pre_wabo_dossiers()
        bd = models.BouwDossier.objects.get(dossiernr=3)
        self.assertEqual(bd.stadsdeel, 'SA')
        self.assertEqual(bd.titel, "Hoogte Kadijk 40")
        self.assertEqual(bd.datering.strftime("%Y"), "2003")
        self.assertEqual(bd.dossier_type, "verbouwing")
        self.assertEqual(bd.access, "PUBLIC")
        self.assertEqual(bd.source, "EDEPOT")
        adres0 = bd.adressen.first()
        self.assertEqual(adres0.straat, "Hoogte Kadijk")
        self.assertEqual(adres0.huisnummer_van, 40)
        self.assertEqual(adres0.huisnummer_tot, 40)
        document0 = bd.documenten.first()
        self.assertEqual(document0.barcode, "SA00000007")
        self.assertEqual(document0.subdossier_titel, "Aanvraag en behandeling")
        self.assertEqual(document0.bestanden, [
            "SA/00003/SA00000007_00001.jpg",
            "SA/00003/SA00000007_00002.jpg",
            "SA/00003/SA00000007_00003.jpg"
        ])
        self.assertEqual(document0.access, "PUBLIC")
        bd123 = models.BouwDossier.objects.get(dossiernr=123)
        for document123 in bd123.documenten.all():
            if document123.barcode == "SA00001038":
                self.assertEqual(document123.access, "RESTRICTED")
            elif document123.barcode == "SA00001039":
                self.assertEqual(document123.access, "PUBLIC")

    def test_wabo_import(self):
        batch.import_wabo_dossiers()
        bd = models.BouwDossier.objects.get(dossiernr=51322878)
        self.assertEqual(bd.stadsdeel, 'SDW')
        self.assertEqual(bd.titel, "MK Sloopmelding asbestverwijdering bij mutatie- en klachtenonderhoud op het adres Van Hallstraat\n\t\t\t64 AMSTERDAM - (Portiekflat)")
        self.assertEqual(bd.datering.strftime("%Y"), "2013")
        self.assertEqual(bd.dossier_type, "sloopmelding")
        self.assertEqual(bd.access, "RESTRICTED")
        self.assertEqual(bd.source, "WABO")
        self.assertEqual(bd.olo_liaan_nummer, 831835)
        self.assertEqual(bd.wabo_bron, "SquitXO")
        adres0 = bd.adressen.first()
        self.assertEqual(adres0.straat, "Van Hallstraat")
        self.assertEqual(adres0.huisnummer_van, 64)
        self.assertEqual(adres0.huisnummer_tot, None)
        self.assertEqual(adres0.openbareruimte_id, "0363300000005205")
        self.assertEqual(adres0.verblijfsobjecten, ['0363010000839320'])
        self.assertEqual(adres0.panden, ['0363100012133317'])
        documenten = bd.documenten.order_by('id').all()
        self.assertEqual(len(documenten), 13)
        document12 = documenten[12]
        self.assertEqual(document12.document_omschrijving, "Procesoverzicht")
        self.assertEqual(document12.bestanden, ['SDW/ACTIVITY_DOCS/Procesinformatie sdw_51322878.pdf'])
        self.assertEqual(document12.oorspronkelijk_pad, ['F:/INZAGEDOCS/SDW/ACTIVITY_DOCS/Procesinformatie sdw_51322878.pdf'])

        # This also tests import of PREWABO dossiers for KEY2 tussenbestand. To the stadsdeel P will be appendend
        bd1 = models.BouwDossier.objects.get(dossiernr=94076, stadsdeel='SDCP')
        # self.assertEqual(bd1.stadsdeel, 'SDCP')
        self.assertEqual(bd1.titel, "Het veranderen van de voorgevel van het gebouwgedeelte Nieuwendijk 200/202")
        self.assertEqual(bd1.datering.strftime("%Y"), "2009")
        self.assertEqual(bd1.dossier_type, "bouwvergunning")
        self.assertEqual(bd1.access, "RESTRICTED")
        self.assertEqual(bd1.source, "WABO")
        self.assertEqual(bd1.olo_liaan_nummer, 0)
        self.assertEqual(bd1.wabo_bron, "KEY2")
        adres1 = bd1.adressen.first()
        self.assertEqual(adres1.straat, "Nieuwendijk")
        self.assertEqual(adres1.huisnummer_van, 200)
        self.assertEqual(adres1.huisnummer_tot, None)
        self.assertEqual(adres1.openbareruimte_id, "0363300000003873")
        self.assertEqual(adres1.verblijfsobjecten, ['0363010001022066'])
        self.assertEqual(adres1.panden, ['0363100012168047'])
        documenten1 = bd1.documenten.order_by('id').all()
        self.assertEqual(len(documenten1), 10)
        document9 = documenten1[9]
        self.assertEqual(document9.document_omschrijving, "Procesoverzicht")
        self.assertEqual(document9.bestanden, ['SDC_PREWABO/ACTIVITY_DOCS/Procesinformatie sdc_prewabo_94076.pdf'])
        self.assertEqual(document9.oorspronkelijk_pad, ['D:/INZAGE_ACTIVITY/SDC_PREWABO/ACTIVITY_DOCS/Procesinformatie sdc_prewabo_94076.pdf'])

