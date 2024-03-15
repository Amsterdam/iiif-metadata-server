import logging
from django.conf import settings

from django.core.management.base import BaseCommand

from bag.bag_loader import BagLoader
from bag.koppeltabel_loader import KoppeltabelLoader
from importer.batch import (add_bag_ids_to_pre_wabo, add_bag_ids_to_wabo,
                            import_pre_wabo_dossiers, import_wabo_dossiers, 
                            validate_import)
from importer.util_azure import download_all_files_from_container, download_blob_to_file, remove_directory
from importer.util_db import (swap_tables_between_apps, truncate_tables)

BAG_SOURCE_SKIP = 0
BAG_SOURCE_API = 1
BAG_SOURCE_AZURE_STORAGE = 2

log = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Import (pre)WABO dossiers and combine with BAG data from datadienst export"

    def import_bag_from_api(self):
        log.info('Importing bag data from api')
        bag = BagLoader()
        truncate_tables(['bag'])

        bag.import_tables_from_endpoint()

        # The link between Pand and Verblijfsobject is not available through the CSV API and needs to be
        # constructed manually
        koppeltabel = KoppeltabelLoader()
        koppeltabel.load()

    def import_bag_from_azure_storage(self):
        log.info('Importing bag data from azure storage')
        bag = BagLoader()
        truncate_tables(['bag'])

        output_dir = f"{settings.DATA_DIR}/bag"
        tables = bag.tables
        tables['bag_verblijfsobjectpandrelatie'] = ''
        files = {}
        for table, _ in tables.items():
            files[table] = download_blob_to_file(settings.AZURE_CONTAINER_NAME_BAG, f"{table}.csv", output_dir)

        bag.load_tables_from_csv(files)

    def import_dossiers(self, dossier_path):
        log.info('Importing pre wabo dossiers')
        import_pre_wabo_dossiers(dossier_path)
        add_bag_ids_to_pre_wabo()
        
        log.info('Importing wabo dossiers')
        import_wabo_dossiers(dossier_path)
        add_bag_ids_to_wabo()

    def add_arguments(self, parser):
        parser.add_argument(
            '--bag_source',
            dest='bag_source',
            type=int,
            default=BAG_SOURCE_AZURE_STORAGE,
            help='Bag data source')
                
        parser.add_argument(
            '--skipgetfiles',
            action='store_true',
            dest='skipgetfiles',
            default=False,
            help='Skip getting files from objectstore')
         
        parser.add_argument(
            '--min_bouwdossiers_count',
            dest='min_bouwdossiers_count',
            type=int,
            default=10000,
            help='Minimum amount of bouwdossiers to be added')
        
    def handle(self, *args, **options):
        log.info('Metadata import started')

        try:
            if options['bag_source'] == BAG_SOURCE_API:
                self.import_bag_from_api()
            elif options['bag_source'] == BAG_SOURCE_AZURE_STORAGE:
                self.import_bag_from_azure_storage()

            dossier_path = settings.DATA_DIR
            if not options['skipgetfiles']:
                dossier_path = f"{settings.DATA_DIR}/dossiers"
                remove_directory(dossier_path)
                download_all_files_from_container(settings.AZURE_CONTAINER_NAME_DOSSIERS, dossier_path)

            truncate_tables(['importer'])
            self.import_dossiers(dossier_path)

            validate_import(options['min_bouwdossiers_count'])

            swap_tables_between_apps('importer', 'bouwdossiers')


        except Exception as e:
            raise Exception(
                "An exception occurred importing the metadata."
            ) from e