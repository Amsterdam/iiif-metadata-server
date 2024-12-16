import csv
import io
from unittest import mock

from django.test import TestCase, override_settings
from model_bakery import baker
from parameterized import parameterized

from bag.constants import (
    BAG_TYPE_LIGPLAATS,
    BAG_TYPE_NUMMERAANDUIDING,
    BAG_TYPE_OPENBARE_RUIMTE,
    BAG_TYPE_PAND,
    BAG_TYPE_STANDPLAATS,
    BAG_TYPE_VERBLIJFSOBJECT,
)
from bag.exceptions import (
    BagIdException,
    IncorrectBagIdLengthException,
    IncorrectGemeenteCodeException,
    IncorrectObjectTypeException,
)
from bag.models import Ligplaats, Standplaats, Verblijfsobject
from bag.utils import BagHelper, read_csv

gemeente_code = "1234"


@override_settings(GEMEENTE_CODE=gemeente_code)
class UtilsTestCase(TestCase):
    @parameterized.expand(["", (None,)])
    def test_get_object_type_empty_param(self, _id):
        with self.assertRaises(BagIdException):
            BagHelper.get_object_type_from_id(_id)

    @parameterized.expand(
        ["01234000000000000", "012345678901234", "123"]  # too long  # too short
    )
    def test_get_object_type_incorrect_length(self, _id):
        with self.assertRaises(IncorrectBagIdLengthException):
            BagHelper.get_object_type_from_id(_id)

    def test_get_object_type_incorrect_gemeente_code(self):
        _id = "0123400000000000"
        with self.assertRaises(IncorrectGemeenteCodeException):
            BagHelper.get_object_type_from_id(_id)

    @parameterized.expand(
        [
            (f"{gemeente_code}{BAG_TYPE_PAND}0000000000", BAG_TYPE_PAND),
            (
                f"{gemeente_code}{BAG_TYPE_NUMMERAANDUIDING}0000000000",
                BAG_TYPE_NUMMERAANDUIDING,
            ),
            (
                f"{gemeente_code}{BAG_TYPE_OPENBARE_RUIMTE}0000000000",
                BAG_TYPE_OPENBARE_RUIMTE,
            ),
            (
                f"{gemeente_code}{BAG_TYPE_VERBLIJFSOBJECT}0000000000",
                BAG_TYPE_VERBLIJFSOBJECT,
            ),
            (f"{gemeente_code}{BAG_TYPE_LIGPLAATS}0000000000", BAG_TYPE_LIGPLAATS),
            (f"{gemeente_code}{BAG_TYPE_STANDPLAATS}0000000000", BAG_TYPE_STANDPLAATS),
        ]
    )
    def test_get_object_type(self, id, expected_type):
        obj_type = BagHelper.get_object_type_from_id(id)
        self.assertEqual(obj_type, expected_type)

    def test_get_object_incorrect_object_type(self):
        valid_object_types = [
            BAG_TYPE_VERBLIJFSOBJECT,
            BAG_TYPE_LIGPLAATS,
            BAG_TYPE_STANDPLAATS,
        ]
        for i in range(100):
            object_type = f"{i:02}"
            id = f"{gemeente_code}{object_type}0000000000"
            if object_type not in valid_object_types:
                with self.assertRaises(IncorrectObjectTypeException):
                    BagHelper.get_object_from_id(id)

    @parameterized.expand(
        [
            (BAG_TYPE_VERBLIJFSOBJECT, Verblijfsobject),
            (BAG_TYPE_LIGPLAATS, Ligplaats),
            (BAG_TYPE_STANDPLAATS, Standplaats),
        ]
    )
    @mock.patch("bag.utils.BagHelper.get_object_type_from_id")
    def test_get_object_doesnotexist(self, object_type, model, mocked_get_obj_type):
        mocked_get_obj_type.return_value = object_type
        with self.assertRaises(model.DoesNotExist):
            BagHelper.get_object_from_id("123456")
            mocked_get_obj_type.assert_called_with("123456")

    @parameterized.expand(
        [BAG_TYPE_VERBLIJFSOBJECT, BAG_TYPE_LIGPLAATS, BAG_TYPE_STANDPLAATS]
    )
    def test_get_object(self, object_type):
        _id = f"{gemeente_code}{object_type}0000000000"
        verblijfsobject = baker.make(Verblijfsobject, id=_id)
        ligplaats = baker.make(Ligplaats, id=_id)
        standplaats = baker.make(Standplaats, id=_id)

        obj = BagHelper.get_object_from_id(_id)
        if object_type == BAG_TYPE_VERBLIJFSOBJECT:
            self.assertEqual(obj, verblijfsobject)
        elif object_type == BAG_TYPE_LIGPLAATS:
            self.assertEqual(obj, ligplaats)
        elif object_type == BAG_TYPE_STANDPLAATS:
            self.assertEqual(obj, standplaats)

    def test_read_csv(self):
        csv_data = mock_csv_from_dict({"identifier": "idval", "column": "colval"})
        with mock.patch("builtins.open", mock.mock_open(read_data=csv_data)):
            rows = list(
                read_csv("mocked", field_mapping={"identifier": "id", "column": "col"})
            )
            assert rows[0]["id"] == "idval"
            assert rows[0]["col"] == "colval"

    def test_read_csv_without_field_mapping(self):
        csv_data = mock_csv_from_dict({"identifier": "idval", "column": "colval"})
        with mock.patch("builtins.open", mock.mock_open(read_data=csv_data)):
            rows = list(read_csv("mocked"))
            assert rows[0]["identifier"] == "idval"
            assert rows[0]["column"] == "colval"


def mock_csv_from_dict(obj):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=obj.keys())
    writer.writeheader()
    writer.writerow(obj)
    return output.getvalue()
