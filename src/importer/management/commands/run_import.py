import logging

from django.core.management.base import BaseCommand


from bag.bag_loader import BagLoader
from bag.koppeltabel_loader import KoppeltabelLoader
from importer.batch import (add_bag_ids_to_pre_wabo, add_bag_ids_to_wabo,
                            import_pre_wabo_dossiers, import_wabo_dossiers, 
                            validate_import)
from importer.util_azure import download_xml_files
from importer.util_db import (swap_tables_between_apps, truncate_tables)


log = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Import (pre)WABO dossiers and combine with BAG data from datadienst export"

    def import_bag(self):
        bag = BagLoader()
        bag.load_all_tables()

        # # The link between Pand and Verblijfsobject is not available through the CSV API and needs to be
        # # constructed manually
        koppeltabel = KoppeltabelLoader()
        koppeltabel.load()

    def import_dossiers(self):
        log.info('Importing pre wabo dossiers')
        import_pre_wabo_dossiers()
        add_bag_ids_to_pre_wabo()
        
        log.info('Importing wabo dossiers')
        import_wabo_dossiers()
        add_bag_ids_to_wabo()

    def add_arguments(self, parser):
        parser.add_argument(
            '--skipgetbag',
            action='store_true',
            dest='skipgetbag',
            default=False,
            help='Skip getting bag data')
                
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
            if not options['skipgetbag']:
                truncate_tables(['bag'])
                self.import_bag()

            if not options['skipgetfiles']:
                truncate_tables(['importer'])
                download_xml_files()

            self.import_dossiers()

            # TODO: Test with previous code if this outputs the same results for the current test dossiers?
            # validate_import(options['min_bouwdossiers_count'])

            swap_tables_between_apps('importer', 'bouwdossiers')


        except Exception as e:
            raise Exception(
                "An exception occurred importing the metadata."
            ) from e