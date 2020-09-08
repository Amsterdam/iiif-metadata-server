from random import randint

from django.conf import settings
from django.urls import reverse
from rest_framework.test import APITestCase

from bouwdossiers.models import SOURCE_WABO, Adres, BouwDossier, Document
from bouwdossiers.tests import factories


def create_bouwdossiers(n, stadsdeel='AA'):
    return [factories.BouwDossierFactory(dossiernr=randint(10, 10000), stadsdeel=stadsdeel,
                                         olo_liaan_nummer=randint(10, 10000)) for i in range(n)]


def delete_all_records():
    BouwDossier.objects.all().delete()
    Adres.objects.all().delete()
    Document.objects.all().delete()


class APITest(APITestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_api_list(self):
        create_bouwdossiers(3)
        url = reverse('bouwdossier-list')
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertGreaterEqual(response.data['count'], 3)
        delete_all_records()

    def test_api_malformed_code(self):
        url = reverse('bouwdossier-detail', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_api_one_using_stadsdeel_and_dossier(self):
        dossiers = create_bouwdossiers(3)
        pk = dossiers[0].stadsdeel + str(dossiers[0].dossiernr)
        url = reverse('bouwdossier-detail', kwargs={'pk': pk})
        response = self.client.get(url)
        self.assertEqual(response.data['stadsdeel'], dossiers[0].stadsdeel)
        self.assertEqual(response.data['dossiernr'], dossiers[0].dossiernr)
        delete_all_records()

    def test_api_one_using_stadsdeel_3_letters(self):
        create_bouwdossiers(3)
        dossier = BouwDossier.objects.first()
        dossier.stadsdeel = 'AAA'
        dossier.save()

        pk = dossier.stadsdeel + str(dossier.dossiernr)
        url = reverse('bouwdossier-detail', kwargs={'pk': pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['stadsdeel'], dossier.stadsdeel)
        self.assertEqual(response.data['dossiernr'], dossier.dossiernr)
        delete_all_records()

    def test_api_one_using_stadsdeel_4_letters(self):
        create_bouwdossiers(3)
        dossier = BouwDossier.objects.first()
        dossier.stadsdeel = 'AAAA'
        dossier.save()

        pk = dossier.stadsdeel + str(dossier.dossiernr)
        url = reverse('bouwdossier-detail', kwargs={'pk': pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['stadsdeel'], dossier.stadsdeel)
        self.assertEqual(response.data['dossiernr'], dossier.dossiernr)
        delete_all_records()

    def test_api_with_lowercase_stadsdeel(self):
        create_bouwdossiers(3)
        dossier = BouwDossier.objects.first()
        dossier.stadsdeel = 'AAA'
        dossier.save()

        pk = dossier.stadsdeel.lower() + str(dossier.dossiernr)
        url = reverse('bouwdossier-detail', kwargs={'pk': pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['stadsdeel'], dossier.stadsdeel)
        self.assertEqual(response.data['dossiernr'], dossier.dossiernr)
        delete_all_records()

    def test_api_with_underscore_between_stadsdeel_and_dossiernr(self):
        create_bouwdossiers(3)
        dossier = BouwDossier.objects.first()
        dossier.stadsdeel = 'AAA'
        dossier.save()

        pk = dossier.stadsdeel + '_' + str(dossier.dossiernr)  # add an underscore
        url = reverse('bouwdossier-detail', kwargs={'pk': pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['stadsdeel'], dossier.stadsdeel)
        self.assertEqual(response.data['dossiernr'], dossier.dossiernr)
        delete_all_records()

    def test_api_with_wrongly_formatted_stadsdeel_dossiernr_combination(self):
        create_bouwdossiers(3)
        dossier = BouwDossier.objects.first()
        dossier.stadsdeel = 'AAA'
        dossier.save()

        pk = "A"
        url = reverse('bouwdossier-detail', kwargs={'pk': pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        delete_all_records()

    def test_dossiernr_stadsdeel(self):
        factories.DocumentFactory(bouwdossier__dossiernr=111)
        factories.AdresFactory(bouwdossier__dossiernr=111)  # Also add an address to the bouwdossier

        # And add two more dossiers to make sure it's only selecting the one we need
        factories.DocumentFactory(bouwdossier__dossiernr=222)
        factories.DocumentFactory(bouwdossier__dossiernr=333)

        url = reverse('bouwdossier-list') + '?dossiernr=111&stadsdeel=AA'
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
        delete_all_records()

    def test_stadsdeel_None(self):
        dossiers = create_bouwdossiers(3)
        url = reverse('bouwdossier-list') + f'?dossiernr={dossiers[0].dossiernr}&stadsdeel=CC'
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 0)
        delete_all_records()

    def test_dossiernr_None(self):
        create_bouwdossiers(3)
        url = reverse('bouwdossier-list') + '?dossiernr=123456&stadsdeel=AA'  # existing stadsdeel, but non existing dossiernr
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 0)
        delete_all_records()

    def test_nummeraanduiding(self):
        factories.AdresFactory()
        factories.AdresFactory()
        adres = factories.AdresFactory()
        adres.nummeraanduidingen = ['1111111111111111']
        adres.save()

        url = reverse('bouwdossier-list') + '?nummeraanduiding=1111111111111111'
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['titel'], 'weesperstraat 113 - 117')
        delete_all_records()

    def test_nummeraanduiding_non_existent(self):
        factories.AdresFactory()
        url = reverse('bouwdossier-list') + '?nummeraanduiding=1111111111111111'
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 0)
        delete_all_records()

    def test_pand(self):
        factories.AdresFactory()
        factories.AdresFactory()
        adres = factories.AdresFactory()
        adres.panden = ['1111111111111111']
        adres.save()

        url = reverse('bouwdossier-list') + '?pand=1111111111111111'
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['titel'], 'weesperstraat 113 - 117')
        delete_all_records()

    def test_verblijfsobject(self):
        factories.AdresFactory()
        factories.AdresFactory()
        adres = factories.AdresFactory()
        adres.verblijfsobjecten = ['1111111111111111']
        adres.save()

        url = reverse('bouwdossier-list') + '?verblijfsobject=1111111111111111'
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['titel'], 'weesperstraat 113 - 117')
        delete_all_records()

    def test_openbareruimte(self):
        factories.AdresFactory()
        factories.AdresFactory()
        adres = factories.AdresFactory()
        adres.openbareruimte_id = '1111111111111111'
        adres.save()

        url = reverse('bouwdossier-list') + '?verblijfsobject=036301000xxxxxxx/?openbareruimte=1111111111111111'
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['titel'], 'weesperstraat 113 - 117')
        delete_all_records()

    def test_dossiernr_stadsdeel_max_datering_none(self):
        create_bouwdossiers(3)
        url = reverse('bouwdossier-list') + '?dossiernr=12345&stadsdeel=AA&max_datering=1997'
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 0)
        delete_all_records()

    def test_dossiernr_stadsdeel_max_datering(self):
        dossiers = create_bouwdossiers(3)

        url = reverse('bouwdossier-list') + f'?dossiernr={dossiers[0].dossiernr}&stadsdeel=AA&max_datering=2000'
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['titel'], 'weesperstraat 113 - 117')
        delete_all_records()

    def test_dossiernr_stadsdeel_min_datering_none(self):
        dossiers = create_bouwdossiers(3)

        url = reverse('bouwdossier-list') + f'?dossiernr={dossiers[0].dossiernr}&stadsdeel=A&min_datering=1999'
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 0)
        delete_all_records()

    def test_dossiernr_stadsdeel_min_datering(self):
        dossiers = create_bouwdossiers(3)

        url = reverse('bouwdossier-list') + f'?dossiernr={dossiers[0].dossiernr}&stadsdeel=AA&min_datering=1997'
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['titel'], 'weesperstraat 113 - 117')
        delete_all_records()

    def test_olo_liaan_nummer(self):
        bd = factories.BouwDossierFactory(olo_liaan_nummer=7777777)
        factories.DocumentFactory(bouwdossier__dossiernr=bd.dossiernr)
        factories.AdresFactory(bouwdossier__dossiernr=bd.dossiernr)  # Also add an address to the bouwdossier

        # And add two more dossiers to make sure it's only selecting the one we need
        factories.BouwDossierFactory(dossiernr=222)
        factories.BouwDossierFactory(dossiernr=333)

        url = reverse('bouwdossier-list') + '?olo_liaan_nummer=7777777'
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['olo_liaan_nummer'], 7777777)
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
        delete_all_records()

    def test_filter_subdossier(self):
        """
        subdossier should match with case insensitive start of titel of subdossier
        """
        factories.DocumentFactory(subdossier_titel='Tekeningen one')
        factories.DocumentFactory(subdossier_titel='Tekeningen two')
        factories.DocumentFactory(subdossier_titel='Tekeningen three')
        factories.DocumentFactory(subdossier_titel='No tekingen')

        url = reverse('bouwdossier-list') + '?subdossier=tekeningen'
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(response.data['results'][0]['titel'], 'weesperstraat 113 - 117')
        delete_all_records()

    def test_subdossier_none(self):
        factories.DocumentFactory(subdossier_titel='One')
        factories.DocumentFactory(subdossier_titel='Two')
        factories.DocumentFactory(subdossier_titel='Three')

        url = reverse('bouwdossier-list') + '?subdossier=dit_match_niet'
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 0)
        delete_all_records()

    def test_dossier_type(self):
        create_bouwdossiers(3)
        factories.BouwDossierFactory(dossier_type='differenttype')

        url = reverse('bouwdossier-list') + '?dossier_type=differenttype'
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['titel'], 'weesperstraat 113 - 117')
        delete_all_records()

    def test_dossier_type_none(self):
        create_bouwdossiers(3)
        url = reverse('bouwdossier-list') + '?dossier_type=non_existing_type'
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 0)
        delete_all_records()

    def test_dossier_with_stadsdeel(self):
        bd = factories.BouwDossierFactory()
        factories.DocumentFactory(bouwdossier__dossiernr=bd.dossiernr)
        factories.AdresFactory(bouwdossier__dossiernr=bd.dossiernr)  # Also add an address to the bouwdossier

        # And add two more dossiers to make sure it's only selecting the one we need
        factories.BouwDossierFactory(dossiernr=222)
        factories.BouwDossierFactory(dossiernr=333)

        url = reverse('bouwdossier-list') + f'?dossier={bd.stadsdeel}{bd.dossiernr}'
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
        delete_all_records()

    def test_dossier_incorrectly_without_stadsdeel(self):
        create_bouwdossiers(3)
        url = reverse('bouwdossier-list') + '?dossier=12345'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        delete_all_records()

    def test_invalid_dossiernr(self):
        create_bouwdossiers(3)
        url = reverse('bouwdossier-list') + '?dossiernr=wrong'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        delete_all_records()

    def test_dossier_wabo_fields(self):
        bd = factories.BouwDossierFactory()
        factories.DocumentFactory(bouwdossier__dossiernr=bd.dossiernr)
        factories.AdresFactory(bouwdossier__dossiernr=bd.dossiernr)  # Also add an address to the bouwdossier

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
        delete_all_records()
