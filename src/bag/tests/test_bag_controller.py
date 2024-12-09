
import pytest
from model_bakery import baker

from bag.bag_controller import BagController
from bag.models import Ligplaats


class TestBagController:
    @pytest.mark.django_db
    def test_upsert_table_data(self):
        obj = baker.prepare(Ligplaats, id="03630000000001", status="Active")
        BagController().upsert_table_data([obj])

        assert Ligplaats.objects.count() == 1
        assert Ligplaats.objects.first().id == "03630000000001"
        assert Ligplaats.objects.first().status == "Active"

    @pytest.mark.django_db
    def test_upsert_table_with_existing_data(self):
        baker.make(Ligplaats, 1, id="03630000000001", status="Inactive")

        obj = baker.prepare(Ligplaats, id="03630000000001", status="Active")
        upserted_keys = BagController().upsert_table_data([obj])

        assert Ligplaats.objects.count() == 1
        assert Ligplaats.objects.first().id == "03630000000001"
        assert Ligplaats.objects.first().status == "Active"
        assert upserted_keys == ["03630000000001"]

    @pytest.mark.django_db
    def test_upsert_table_with_no_changes_in_data(self):
        baker.make(Ligplaats, 1, id="03630000000001", status="Inactive")

        obj = baker.prepare(Ligplaats, id="03630000000001", status="Inactive")
        upserted_keys = BagController().upsert_table_data([obj])

        assert Ligplaats.objects.count() == 1
        assert Ligplaats.objects.first().id == "03630000000001"
        assert Ligplaats.objects.first().status == "Inactive"
        assert upserted_keys == ["03630000000001"]

    @pytest.mark.django_db
    def test_upsert_table_with_new_data(self):
        baker.make(Ligplaats, 1, id="03630000000001")

        obj = baker.prepare(Ligplaats, id="03630000000002", status="Active")
        upserted_keys = BagController().upsert_table_data([obj])

        assert Ligplaats.objects.count() == 2
        assert Ligplaats.objects.all()[0].id == "03630000000001"
        assert Ligplaats.objects.all()[1].id == "03630000000002"
        assert upserted_keys == ["03630000000002"]

    @pytest.mark.django_db
    def test_upsert_table_with_many_data(self):
        baker.make(Ligplaats, 1, id="03630000000001")

        objects = [
            baker.prepare(Ligplaats, id="03630000000001", status="Active"),
            baker.prepare(Ligplaats, id="03630000000002", status="Active"),
        ]
        upserted_keys = BagController().upsert_table_data(objects)

        assert Ligplaats.objects.count() == 2
        assert Ligplaats.objects.all()[0].id == "03630000000001"
        assert Ligplaats.objects.all()[1].id == "03630000000002"
        assert upserted_keys == ["03630000000001", "03630000000002"]

    @pytest.mark.django_db
    def test_upsert_table_with_empty_data(self):
        objects = []
        BagController().upsert_table_data(objects)
        assert Ligplaats.objects.count() == 0

    @pytest.mark.django_db
    def test_delete_nonmodified_table_records(self):
        baker.make(Ligplaats, 1, id="03630000000000")
        baker.make(Ligplaats, 1, id="03630000000001")

        BagController().delete_nonmodified_table_records(Ligplaats, ["03630000000001"])

        assert Ligplaats.objects.count() == 1
        assert Ligplaats.objects.first().id == "03630000000001"

    @pytest.mark.django_db
    def test_delete_nonmodified_table_records_no_change(self):
        baker.make(Ligplaats, 1, id="03630000000000")
        baker.make(Ligplaats, 1, id="03630000000001")

        BagController().delete_nonmodified_table_records(
            Ligplaats, ["03630000000000", "03630000000001"]
        )

        assert Ligplaats.objects.count() == 2
