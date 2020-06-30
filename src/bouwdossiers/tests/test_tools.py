from django.test import TestCase

from bouwdossiers import tools


class ToolstestCase(TestCase):
    def setUp(self):
        pass

    def test_separate_dossier(self):
        # Test default formatting
        stadsdeel, dossiernr = tools.separate_dossier('ABC1234')
        self.assertEquals(stadsdeel, 'ABC')
        self.assertEquals(dossiernr, '1234')

        # Test with underscore formatting
        stadsdeel, dossiernr = tools.separate_dossier('ABC_1234')
        self.assertEquals(stadsdeel, 'ABC')
        self.assertEquals(dossiernr, '1234')

        # Test with lowercase letter stadsdeelcode formatting
        stadsdeel, dossiernr = tools.separate_dossier('abc1234')
        self.assertEquals(stadsdeel, 'ABC')
        self.assertEquals(dossiernr, '1234')

        # Test with underscore and lowercase letter stadsdeelcode formatting
        stadsdeel, dossiernr = tools.separate_dossier('abc_1234')
        self.assertEquals(stadsdeel, 'ABC')
        self.assertEquals(dossiernr, '1234')

        # Test whether wrongly formatted inputs fail
        with self.assertRaises(tools.InvalidDossier):
            tools.separate_dossier('ABC')
        with self.assertRaises(tools.InvalidDossier):
            tools.separate_dossier('1234')
        with self.assertRaises(tools.InvalidDossier):
            tools.separate_dossier('A1234')  # only one letter stadsdeelcode should also fail
        with self.assertRaises(tools.InvalidDossier):
            tools.separate_dossier('AAAA1234')  # four or more letter stadsdeelcodes should also fail
