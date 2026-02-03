from datetime import date
from unittest.mock import patch

import pytest
from model_bakery import baker

from bag.bag_api import Zip
from bag.models import Ligplaats, Pand

from .utils import MockResponse


class TestBagZipApi:
    def test_get_records_models_to_endpoints_undefined(self):
        bag_zip_api = Zip()
        bag_zip_api.model_to_endpoint = {}
        with pytest.raises(AssertionError):
            bag_zip_api.get_records(Ligplaats)

    @patch("bag.bag_api.requests.get")
    def test_download_zip(self, mock_request):
        mock_request.return_value = MockResponse({}, 200, content=b"b")
        path = Zip().download_zip("mocked")
        assert path == "/tmp/mocked"

    @pytest.mark.django_db
    @patch("bag.bag_api.Zip.download_zip")
    @patch("bag.bag_api.Zip.unpack_zip")
    @patch("bag.bag_api.read_csv")
    def test_get_bag_records(self, mock_read_csv, mock_unpack, mock_download):
        api = Zip()
        api.model_to_endpoint = {
            Ligplaats: "gebieden_ligplaatsen.csv.zip",
            Pand: "bag_panden.csv.zip",
        }
        mock_download.side_effect = [
            "/tmp/gebieden_ligplaatsen.csv.zip",
            "/tmp/bag_panden.csv.zip",
        ]
        mock_unpack.side_effect = [
            "/tmp/gebieden_ligplaatsen.csv",
            "/tmp/bag_panden.csv",
        ]
        mock_read_csv.side_effect = [
            [
                x
                for x in [
                    mock_model_data(Ligplaats, id="03630000000001"),
                    mock_model_data(Ligplaats, id="03630000000002"),
                ]
            ],
            [x for x in [mock_model_data(Pand, id="03630000000003")]],
        ]

        baker.make(Pand, id="03630000000000")
        ligplaats_records = list(api.get_records(Ligplaats))
        assert len(ligplaats_records) == 2
        assert ligplaats_records[0].get("id") == "03630000000001"

        pand_records = api.get_records(Pand)
        assert len(pand_records) == 1
        assert pand_records[0].get("id") == "03630000000003"


# Mockdata generation helpers


def mock_model_data(bag_model, **args):
    data = baker.prepare(bag_model, **args).__dict__
    del data["_state"]
    data = {field: f"{val}" if isinstance(val, date) else val for field, val in data.items()}
    return data
