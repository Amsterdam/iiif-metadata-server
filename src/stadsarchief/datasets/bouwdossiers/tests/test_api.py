from rest_framework.test import APITestCase

from stadsarchief.datasets.bouwdossiers.tests import authorization, factories


class APITest(APITestCase, authorization.AuthorizationSetup):

    def setUp(self):
        self.setUpAuthorization()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        factories.BouwDossierFactory()
        factories.DocumentFactory()
        factories.AdresFactory()

    def test_api_list(self):
        url = '/stadsarchief/bouwdossier/'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_scope_bd_r}')
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertGreaterEqual(response.data['count'], 1)

    def test_api_malformed_code(self):
        url = '/stadsarchief/bouwdossier/1/'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_scope_bd_r}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_api_one_using_stadsdeel_and_dossier(self):
        url = '/stadsarchief/bouwdossier/AA12345/'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_scope_bd_r}')
        response = self.client.get(url)
        self.assertEqual(response.data['stadsdeel'], 'AA')
        self.assertEqual(response.data['dossiernr'], 12345)

    def test_dossiernr_stadsdeel(self):
        url = '/stadsarchief/bouwdossier/?dossiernr=12345&stadsdeel=AA'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_scope_bd_r}')
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['titel'], 'weesperstraat 113 - 117')
        self.assertEqual(response.data['results'][0]['documenten'][0]['bestanden'][0], 'SU10000010_00001.jpg')
        self.assertEqual(response.data['results'][0]['documenten'][0]['access'], 'RESTRICTED')
        self.assertEqual(response.data['results'][0]['documenten'][0]['barcode'], 'ST100')
        self.assertEqual(response.data['results'][0]['adressen'][0]['nummeraanduidingen'][0],
                         '0363200000406187')
        self.assertEqual(response.data['results'][0]['adressen'][0]['panden'][0], '0363100012165490')

    def test_dossiernr_stadsdeel_None1(self):
        url = '/stadsarchief/bouwdossier/?dossiernr=12345&stadsdeel=CC'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_scope_bd_r}')
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 0)

    def test_dossiernr_stadsdeel_None2(self):
        url = '/stadsarchief/bouwdossier/?dossiernr=54321&stadsdeel=AA'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_scope_bd_r}')
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 0)

    def test_nummeraanduiding(self):
        url = '/stadsarchief/bouwdossier/?nummeraanduiding=0363200000406187'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_scope_bd_r}')
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['titel'], 'weesperstraat 113 - 117')

    def test_nummeraanduiding_no(self):
        url = '/stadsarchief/bouwdossier/?nummeraanduiding=0363200000406188'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_scope_bd_r}')
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 0)

    def test_pand(self):
        url = '/stadsarchief/bouwdossier/?pand=0363100012165490'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_scope_bd_r}')
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['titel'], 'weesperstraat 113 - 117')

    def test_vbo(self):
        url = '/stadsarchief/bouwdossier/?verblijfsobject=036301000xxxxxxx'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_scope_bd_r}')
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['titel'], 'weesperstraat 113 - 117')

    def test_openbareruimte(self):
        url = '/stadsarchief/bouwdossier/?openbareruimte=0363300000004835'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_scope_bd_r}')
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['titel'], 'weesperstraat 113 - 117')

    def test_dossiernr_stadsdeel_max_datering_none(self):
        url = '/stadsarchief/bouwdossier/?dossiernr=12345&stadsdeel=A&max_datering=1997'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_scope_bd_r}')
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 0)

    def test_dossiernr_stadsdeel_max_datering(self):
        url = '/stadsarchief/bouwdossier/?dossiernr=12345&stadsdeel=AA&max_datering=2000'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_scope_bd_r}')
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['titel'], 'weesperstraat 113 - 117')

    def test_dossiernr_stadsdeel_min_datering_none(self):
        url = '/stadsarchief/bouwdossier/?dossiernr=12345&stadsdeel=A&min_datering=1999'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_scope_bd_r}')
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 0)

    def test_dossiernr_stadsdeel_min_datering(self):
        url = '/stadsarchief/bouwdossier/?dossiernr=12345&stadsdeel=AA&min_datering=1997'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_scope_bd_r}')
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['titel'], 'weesperstraat 113 - 117')

    def test_filter_subdossier(self):
        """
        subdossier should match with case insensitive start of titel of subdossier
        """
        url = '/stadsarchief/bouwdossier/?subdossier=tekeningen'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_scope_bd_r}')
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['titel'], 'weesperstraat 113 - 117')

    def test_subdossier_none(self):
        url = '/stadsarchief/bouwdossier/?subdossier=dit_match_niet'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_scope_bd_r}')
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 0)

    def test_dossier_type(self):
        url = '/stadsarchief/bouwdossier/?dossier_type=verbouwing'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_scope_bd_r}')
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['titel'], 'weesperstraat 113 - 117')

    def test_dossier_type_none(self):
        url = '/stadsarchief/bouwdossier/?dossier_type=geen_type'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_scope_bd_r}')
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 0)
