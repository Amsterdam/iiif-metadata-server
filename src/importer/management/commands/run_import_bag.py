import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from bag import bag_api
from bag.bag_controller import BagController
from bag.models import BagUpdatedAt, Verblijfsobjectpandrelatie

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import BAG data from the API"

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                bag_zip_api = bag_api.Zip()
                bag = BagController()

                upserted_model_keys = {}
                for bag_model in bag_zip_api.model_to_endpoint.keys():
                    if isinstance(bag_model, Verblijfsobjectpandrelatie):
                        continue
                    
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

                # Process the Verblijfsobjectpandrelatie junction table separately after all other objects are processed first
                records = bag_zip_api.get_records(Verblijfsobjectpandrelatie)
                records = bag.filter_valid_references(
                    # Threshold (100) 06-12-24 tijdelijk hoog gezet want rijtjeshuizen berekening staat uit, bag import belangrijker
                    Verblijfsobjectpandrelatie, records, threshold=100
                )
                upserted_model_keys_verblijfsobjectpandrelatie = list(
                    bag.upsert_records_in_database(Verblijfsobjectpandrelatie, records)
                )
                bag.delete_nonmodified_table_records(
                    Verblijfsobjectpandrelatie, upserted_model_keys_verblijfsobjectpandrelatie
                )
                
                # We determine the rijtjeshuizen through raw SQL queries
                bag.create_rijtjeshuizen_tables()

                # save timestamp separately in db
                BagUpdatedAt().save()

            logger.info(
                f"Bag import succeeded, updated_at {BagUpdatedAt.objects.last().updated_at}"
            )

        except Exception as e:
            logger.exception(
                f"An exception occurred importing the BAG. All operations aborted, database rolled back. Error: {e}"
            )
