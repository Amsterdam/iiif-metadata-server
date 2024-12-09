import logging
from datetime import datetime

from isodate import parse_date, parse_datetime
from toolz import interleave, partial, pipe

from bag.models import Nummeraanduiding, Pand
from bag.utils import chunk_data

logger = logging.getLogger(__name__)


class BagController:
    def create_bag_instances(self, bag_model, row: dict):
        bag_dict = {}
        for field, value in row.items():
            if field not in bag_model.get_fields():
                continue
            if not value and field in bag_model.get_null_fields():
                bag_dict[field] = None
                continue
            if field in bag_model.get_foreign_key_fields():
                field = f"{field}_id"
            if field in bag_model.get_date_fields():
                value = (
                    parse_datetime(value)
                    if "T" in value
                    else datetime.combine(parse_date(value), datetime.now().time())
                )
            bag_dict[field] = value

        try:
            return bag_model(**bag_dict)
        except Exception as e:
            raise e

    def is_valid_object(self, obj):
        # TEMPORARY: Remove when api returns object for specified api urls
        return (
            not (
                # https://api.data.amsterdam.nl/v1/bag/verblijfsobjecten/0363010012582763
                # or https://api.data.amsterdam.nl/v1/bag/nummeraanduidingen/?adresseertVerblijfsobject.identificatie=0363010012582763
                isinstance(obj, Nummeraanduiding)
                and obj.verblijfsobject_id == "0363010012582763"
            )
            and not (
                # https://api.data.amsterdam.nl/v1/bag/verblijfsobjecten/0363010011290888
                # or https://api.data.amsterdam.nl/v1/bag/nummeraanduidingen/?adresseertVerblijfsobject.identificatie=0363010011290888
                isinstance(obj, Nummeraanduiding)
                and obj.verblijfsobject_id == "0363010011290888"
            )
            and not (isinstance(obj, Pand))
        )

    def upsert_table_data(self, bag_objects: iter):
        """Import a table from a csv file"""
        rows = list(bag_objects)
        if not rows:
            logger.warning("- upsert_table_data with empty bag_objects argument")
            return []
        bag_model = rows[0]._meta.model

        if not all(isinstance(obj, bag_model) for obj in rows):
            raise Exception("All objects should be an instance of the same model")

        fields = [field.name for field in bag_model._meta.fields]
        unique_field = bag_model._meta.pk.name
        update_fields = list(filter(lambda field: field != unique_field, fields))

        res = bag_model.objects.bulk_create(
            rows,
            update_conflicts=True,
            update_fields=update_fields,
            unique_fields=[unique_field],
            batch_size=None,
        )
        return [o.pk for o in res]

    def upsert_records_in_database(self, bag_model, records):
        logger.info(f"Upserting records in {bag_model}")

        return pipe(
            records,
            partial(map, partial(self.create_bag_instances, bag_model)),
            partial(filter, self.is_valid_object),
            partial(chunk_data, chunk_size=1000),
            partial(map, self.upsert_table_data),
            interleave,
        )

    @staticmethod
    def delete_nonmodified_table_records(bag_model, upserted_pk_indices: list[int]):
        logger.info(f"Deleting records from {bag_model}")
        num_deleted, _ = bag_model.objects.exclude(pk__in=upserted_pk_indices).delete()
        logger.info(f"Deleted {num_deleted} records from {bag_model}")
