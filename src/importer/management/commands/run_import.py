import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from bag import bag_api
from bag.bag_controller import BagController
from bag.models import BagUpdatedAt

from importer.batch import (
    add_bag_ids_to_pre_wabo,
    add_bag_ids_to_wabo,
    import_pre_wabo_dossiers,
    import_wabo_dossiers,
    validate_import,
)
from importer.util_azure import (
    download_all_files_from_container,
    download_blob_to_file,
    remove_directory,
)
from importer.util_db import swap_tables_between_apps, truncate_tables

BAG_SOURCE_SKIP = 0
BAG_SOURCE_API = 1
BAG_SOURCE_AZURE_STORAGE = 2

log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import (pre)WABO dossiers and combine with BAG data from datadienst export"

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

            # We determine the rijtjeshuizen through raw SQL queries
            bag.create_rijtjeshuizen_tables()

            # save timestamp separately in db
            BagUpdatedAt().save()

            logger.info(
                f"Bag import succeeded, updated_at {BagUpdatedAt.objects.last().updated_at}"
            )

    def import_bag_from_azure_storage(
        self,
    ):  # TODO: Vraag Terry of we dit nog gebruiken
        log.info("Importing bag data from azure storage")
        bag = BagLoader()
        truncate_tables(["bag"])

        output_dir = f"{settings.DATA_DIR}/bag"
        tables = bag.tables
        tables["bag_verblijfsobjectpandrelatie"] = ""
        files = {}
        for table, _ in tables.items():
            files[table] = download_blob_to_file(
                settings.AZURE_CONTAINER_NAME_BAG, f"{table}.csv", output_dir
            )

        bag.load_tables_from_csv(files)

    def import_dossiers(self, dossier_path):
        log.info("Importing pre wabo dossiers")
        import_pre_wabo_dossiers(dossier_path)
        add_bag_ids_to_pre_wabo()

        log.info("Importing wabo dossiers")
        import_wabo_dossiers(dossier_path)
        add_bag_ids_to_wabo()

    def add_arguments(self, parser):
        parser.add_argument(
            "--bag_source",
            dest="bag_source",
            type=int,
            default=BAG_SOURCE_AZURE_STORAGE,
            help="Bag data source",
        )

        parser.add_argument(
            "--skipgetfiles",
            action="store_true",
            dest="skipgetfiles",
            default=False,
            help="Skip getting files from objectstore",
        )

        parser.add_argument(
            "--min_bouwdossiers_count",
            dest="min_bouwdossiers_count",
            type=int,
            default=settings.MIN_BOUWDOSSIERS_COUNT,
            help="Minimum amount of bouwdossiers to be added",
        )

    def handle(self, *args, **options):
        log.info("Metadata import started")

        try:
            if options["bag_source"] == BAG_SOURCE_API:
                self.import_bag_from_api()
            elif options["bag_source"] == BAG_SOURCE_AZURE_STORAGE:
                self.import_bag_from_azure_storage()

            dossier_path = settings.DATA_DIR
            if not options["skipgetfiles"]:
                dossier_path = f"{settings.DATA_DIR}/dossiers"
                remove_directory(dossier_path)
                download_all_files_from_container(
                    settings.AZURE_CONTAINER_NAME_DOSSIERS, dossier_path
                )

            truncate_tables(["importer"])
            self.import_dossiers(dossier_path)

            validate_import(options["min_bouwdossiers_count"])

            swap_tables_between_apps("importer", "bouwdossiers")

        except Exception as e:
            raise Exception("An exception occurred importing the metadata.") from e
