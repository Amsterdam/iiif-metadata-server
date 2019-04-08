from rest_framework.test import APITestCase

from stadsarchief.datasets.bouwdossiers.tests import authorization, factories


class APITest(APITestCase, authorization.AuthorizationSetup):

    def setUp(self):
        self.setUpAuthorization()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        factories.BouwDossierFactory()
        factories.SubDossierFactory()
        factories.AdresFactory()
        factories.BestandFactory()
        factories.NummeraanduidingFactory()
        factories.PandFactory()

    def test_dossiernr_stadsdeel(self):
        url = '/stadsarchief/bouwdossier/?dossiernr=12345&stadsdeel=A'
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer {}'.format(self.token_scope_bd_r))
        response = self.client.get(url)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['titel'], 'weesperstraat 113 - 117')
        self.assertEqual(response.data['results'][0]['subdossiers'][0]['bestanden'][0]['name'], 'SU10000010_00001.jpg')
        self.assertEqual(response.data['results'][0]['adressen'][0]['nummeraanduidingen'][0]['landelijk_id'],
                         '0363200000406187')
        self.assertEqual(response.data['results'][0]['adressen'][0]['panden'][0]['landelijk_id'], '0363100012165490')





