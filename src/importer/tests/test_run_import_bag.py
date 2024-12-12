import itertools
from unittest.mock import patch

import pytest
from django.core.management import call_command

from bag.bag_api import Zip
from bag.models import (
    Ligplaats,
    Nummeraanduiding,
    Openbareruimte,
    Pand,
    Standplaats,
    Verblijfsobject,
    Verblijfsobjectpandrelatie,
)


class TestBagImportBag:
    @pytest.mark.django_db
    @pytest.mark.parametrize("model,endpoint", [
        (Ligplaats, "bag_ligplaatsen.csv.zip"),
        (Openbareruimte, "bag_openbareruimtes.csv.zip"),
        (Standplaats, "bag_standplaatsen.csv.zip"),
        (Pand, "bag_panden.csv.zip"),
        (Verblijfsobject, "bag_verblijfsobjecten.csv.zip"),
        # (Nummeraanduiding, "bag_nummeraanduidingen.csv.zip"),  # Skip this file as it depends on other CSV files being imported
        (Verblijfsobjectpandrelatie, "benkagg_bagpandbevatverblijfsobjecten.csv.zip"),
    ])
    def test_import_bag_handle(self, model, endpoint):
        """
        This test verifies that the 'run_import_bag' command correctly handles
        the import process by patching the 'get_records' method of the 'Zip' class
        and the model_to_endpoint class variable.

        The patched method will return only the first five records from the original
        implementation, allowing for controlled testing of the import functionality.

        The patched class variable, using parameterize, makes sure that every csv is
        tested in a separate test.
        """
        # Keep the original, unpatched, class method "get_records"
        original_get_records = Zip.get_records

        with (patch.object(Zip, "get_records", autospec=True) as mock_get_records,
              patch.object(Zip, "model_to_endpoint", new={model: endpoint})):

            def side_effect(self, bag_model):
                """
                Call the original class methods get_records and only return the 5 first items as a generator
                """
                original_result = original_get_records(self, bag_model=bag_model)
                return itertools.islice(original_result, 5)

            mock_get_records.side_effect = side_effect

            # Call the management command
            call_command("run_import_bag")
