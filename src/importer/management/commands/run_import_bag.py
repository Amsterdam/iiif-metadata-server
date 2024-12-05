import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from bag import bag_api
from bag.bag_controller import BagController
from bag.models import BagUpdatedAt

log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import BAG data from the API"

    def import_bag_from_api(self):
        with transaction.atomic():
            bag_zip_api = bag_api.Zip()
            bag = BagController()

            upserted_model_keys = {}
            for bag_model in bag_zip_api.model_to_endpoint.keys():
                records = bag_zip_api.get_records(bag_model)
                upserted_model_keys[bag_model] = list(
                    bag.upsert_records_in_database(bag_model, records)
                )

            # Reversed order because of foreign key dependencies
            reversed_model_keys = reversed(upserted_model_keys.keys())
            for bag_model in reversed_model_keys:
                bag.delete_nonmodified_table_records(
                    bag_model, upserted_model_keys.get(bag_model)
                )

            # save timestamp separately in db
            BagUpdatedAt().save()

            log.info(
                f"Bag import succeeded, updated_at {BagUpdatedAt.objects.last().updated_at}"
            )

    def handle(self, *args, **options):
        log.info("BAG import started")

        try:
            self.import_bag_from_api()
            log.info("BAG import completed successfully.")
        except Exception as e:
            log.error("An error occurred during the BAG import.")
            raise e
