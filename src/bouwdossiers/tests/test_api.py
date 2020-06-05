from django.conf import settings
from django.urls import reverse
from rest_framework.test import APITestCase

from bouwdossiers.models import SOURCE_WABO, BouwDossier
from bouwdossiers.tests import factories


class APITest(APITestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        factories.BouwDossierFactory()
        factories.DocumentFactory()
        factories.AdresFactory()

    def test_api_list(self):
        url = reverse('bouwdossier-list')
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertGreaterEqual(response.data['count'], 1)

    def test_api_malformed_code(self):
        url = reverse('bouwdossier-detail', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_api_one_using_stadsdeel_and_dossier(self):
        url = reverse('bouwdossier-detail', kwargs={'pk': 'AA12345'})
        response = self.client.get(url)
        self.assertEqual(response.data['stadsdeel'], 'AA')
        self.assertEqual(response.data['dossiernr'], 12345)

    def test_api_one_using_stadsdeel_3_letters(self):
        dossier = BouwDossier.objects.first()
        dossier.stadsdeel = 'AAA'
        dossier.save()

        url = reverse('bouwdossier-detail', kwargs={'pk': 'AAA12345'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['stadsdeel'], 'AAA')
        self.assertEqual(response.data['dossiernr'], 12345)

    def test_dossiernr_stadsdeel(self):
        url = reverse('bouwdossier-list') + '?dossiernr=12345&stadsdeel=AA'
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['titel'], 'weesperstraat 113 - 117')
        self.assertEqual(response.data['results'][0]['documenten'][0]['bestanden'][0]['filename'],
                         'SU10000010_00001.jpg')
        self.assertEqual(response.data['results'][0]['documenten'][0]['bestanden'][0]['url'],
                         f"{settings.IIIF_BASE_URL}edepot:SU10000010_00001.jpg")
        self.assertEqual(response.data['results'][0]['documenten'][0]['access'], 'RESTRICTED')
        self.assertEqual(response.data['results'][0]['documenten'][0]['barcode'], 'ST100')
        self.assertEqual(response.data['results'][0]['adressen'][0]['nummeraanduidingen'][0],
                         '0363200000406187')
        self.assertEqual(response.data['results'][0]['adressen'][0]['panden'][0], '0363100012165490')

    def test_dossiernr_stadsdeel_None1(self):
        url = reverse('bouwdossier-list') + '?dossiernr=12345&stadsdeel=CC'
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 0)

    def test_dossiernr_stadsdeel_None2(self):
        url = reverse('bouwdossier-list') + '?dossiernr=54321&stadsdeel=AA'
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 0)

    def test_nummeraanduiding(self):
        url = reverse('bouwdossier-list') + '?nummeraanduiding=0363200000406187'
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['titel'], 'weesperstraat 113 - 117')

    def test_nummeraanduiding_no(self):
        url = reverse('bouwdossier-list') + '?nummeraanduiding=0363200000406188'
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 0)

    def test_pand(self):
        url = reverse('bouwdossier-list') + '?pand=0363100012165490'
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['titel'], 'weesperstraat 113 - 117')

    def test_vbo(self):
        url = reverse('bouwdossier-list') + '?verblijfsobject=036301000xxxxxxx'
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['titel'], 'weesperstraat 113 - 117')

    def test_openbareruimte(self):
        url = reverse('bouwdossier-list') + '?verblijfsobject=036301000xxxxxxx/?openbareruimte=0363300000004835'
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['titel'], 'weesperstraat 113 - 117')

    def test_dossiernr_stadsdeel_max_datering_none(self):
        url = reverse('bouwdossier-list') + '?dossiernr=12345&stadsdeel=A&max_datering=1997'
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 0)

    def test_dossiernr_stadsdeel_max_datering(self):
        url = reverse('bouwdossier-list') + '?dossiernr=12345&stadsdeel=AA&max_datering=2000'
        print(url)
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['titel'], 'weesperstraat 113 - 117')

    def test_dossiernr_stadsdeel_min_datering_none(self):
        url = reverse('bouwdossier-list') + '?dossiernr=12345&stadsdeel=A&min_datering=1999'
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 0)

    def test_dossiernr_stadsdeel_min_datering(self):
        url = reverse('bouwdossier-list') + '?dossiernr=12345&stadsdeel=AA&min_datering=1997'
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['titel'], 'weesperstraat 113 - 117')

    def test_filter_subdossier(self):
        """
        subdossier should match with case insensitive start of titel of subdossier
        """
        url = reverse('bouwdossier-list') + '?subdossier=tekeningen'
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['titel'], 'weesperstraat 113 - 117')

    def test_subdossier_none(self):
        url = reverse('bouwdossier-list') + '?subdossier=dit_match_niet'
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 0)

    def test_dossier_type(self):
        url = reverse('bouwdossier-list') + '?dossier_type=verbouwing'
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['titel'], 'weesperstraat 113 - 117')

    def test_dossier_type_none(self):
        url = reverse('bouwdossier-list') + '?dossier_type=geen_type'
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 0)

    def test_dossier_with_stadsdeel(self):
        url = reverse('bouwdossier-list') + '?dossier=AA12345'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['titel'], 'weesperstraat 113 - 117')
        self.assertEqual(response.data['results'][0]['documenten'][0]['bestanden'][0]['filename'],
                         'SU10000010_00001.jpg')
        self.assertEqual(response.data['results'][0]['documenten'][0]['bestanden'][0]['url'],
                         f"{settings.IIIF_BASE_URL}edepot:SU10000010_00001.jpg")
        self.assertEqual(response.data['results'][0]['documenten'][0]['access'], 'RESTRICTED')
        self.assertEqual(response.data['results'][0]['documenten'][0]['barcode'], 'ST100')
        self.assertEqual(response.data['results'][0]['adressen'][0]['nummeraanduidingen'][0],
                         '0363200000406187')
        self.assertEqual(response.data['results'][0]['adressen'][0]['panden'][0], '0363100012165490')

    def test_wrong_dossier_with_stadsdeel(self):
        url = reverse('bouwdossier-list') + '?dossier=12345'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_invalid_dossiernr(self):
        url = reverse('bouwdossier-list') + '?dossiernr=wrong'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_dossier_wabo_fields(self):
        dossier = BouwDossier.objects.get(stadsdeel='AA', dossiernr='12345')
        dossier.olo_liaan_nummer = '67890'
        dossier.wabo_bron = 'test'
        dossier.source = SOURCE_WABO
        dossier.save()

        document = dossier.documenten.first()
        document.bestanden = ['https://conversiestraatwabo.amsterdam.nl/webDAV/SDC/PUA/1234567.PDF']
        document.barcode = document.bestanden[0].split('/')[-1].split('.')[0]
        document.oorspronkelijk_pad = ['/path/to/bestand']
        document.save()

        adres = dossier.adressen.first()
        adres.locatie_aanduiding = 'aanduiding'
        adres.huisnummer_letter = 'A'
        adres.huisnummer_toevoeging = 'B'
        adres.save()

        url = reverse('bouwdossier-detail', kwargs={'pk': 'AA12345'})
        response = self.client.get(url)
        documents = response.data.get('documenten')
        adressen = response.data['adressen']
        self.assertEqual(response.data['olo_liaan_nummer'], 67890)
        self.assertEqual(response.data.get('wabo_bron'), None)  # Bron is not needed in the api Check model
        self.assertEqual(documents[0]['oorspronkelijk_pad'], ['/path/to/bestand'])
        self.assertEqual(documents[0]['bestanden'][0]['url'], f"{settings.IIIF_BASE_URL}wabo:AA-12345-67890_1234567")
        self.assertEqual(adressen[0]['locatie_aanduiding'], 'aanduiding')
        self.assertEqual(adressen[0]['huisnummer_letter'], 'A')
        self.assertEqual(adressen[0]['huisnummer_toevoeging'], 'B')
