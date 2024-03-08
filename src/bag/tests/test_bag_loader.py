import logging

from django.conf import settings
from django.db import connection
from django.test import TestCase

from bag.bag_loader import BagLoader

log = logging.getLogger(__name__)

class APITest(TestCase):
    @classmethod

    def setUp(self):
        settings.DATA_DIR = 'bag/tests/data'

    def test_preprocess_csv(self):
        csv_path_input = f"{settings.DATA_DIR}/bag_panden_duplicate_id.csv"
        csv_path_output = f"{settings.DATA_DIR}/bag_panden_filtered.csv"
        with open(csv_path_input) as fpand:
            pand_data = fpand.read()
            self.assertIn("0457100000068588,1", pand_data)

        bag = BagLoader()
        bag.preprocess_csv(csv_path_input, csv_path_output)

        with open(csv_path_output) as fpand:
            pand_data = fpand.read()
            self.assertNotIn("0457100000068588,1", pand_data)
            self.assertIn("0457100000068588,3", pand_data)



