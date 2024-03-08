import logging

from django.conf import settings
from django.test import TestCase

from bag.bag_loader import BagLoader

log = logging.getLogger(__name__)

class MockWriter:
    content = []

    def writeheader(self):
        pass
    
    def writerow(self, row):
        self.content.append(row)

    def __str__(self):
        return list(self.content.values())


class APITest(TestCase):
    @classmethod

    def setUp(self):
        settings.DATA_DIR = 'bag/tests/data'

    def test_preprocess_csv(self):
        csv_data = [
            {"Identificatie": "0457100000068588", "Volgnummer": "3"},
            {"Identificatie": "0457100000068549", "Volgnummer": "3"},
            {"Identificatie": "0457100000068588", "Volgnummer": "1"}
        ]

        reader = iter(csv_data)
        writer = MockWriter()
        bag = BagLoader()
        bag.preprocess_csv_rows(reader, writer)

        self.assertNotIn({'Identificatie': '0457100000068588', 'Volgnummer': '1'}, writer.content)
        self.assertIn({'Identificatie': '0457100000068588', 'Volgnummer': '3'}, writer.content)
        self.assertIn({'Identificatie': '0457100000068549', 'Volgnummer': '3'}, writer.content)


