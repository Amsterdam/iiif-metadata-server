import logging

from django.core.management.base import BaseCommand

from bag.bag_loader import BagLoader
from bag.koppeltabel_loader import KoppeltabelLoader
from importer.batch import (add_bag_ids_to_pre_wabo, add_bag_ids_to_wabo,
                            import_pre_wabo_dossiers, import_wabo_dossiers)

logger = logging.getLogger(__name__)


class BagRetrievalError(Exception):
    pass

# TODO: This command should accept options to modify its behaviour
class Command(BaseCommand):
    help = "Import (pre)WABO dossiers and combine with BAG data from datadienst export"

    def import_bag(self):
        bag = BagLoader()
        bag.truncate_bag_tables_cascade()
        bag.load_all_tables()

        # # The link between Pand and Verblijfsobject is not available through the CSV API and needs to be
        # # constructed manually
        koppeltabel = KoppeltabelLoader()
        koppeltabel.load()

    def import_dossiers(self):
        logger.info('Importing pre wabo dossiers')
        import_pre_wabo_dossiers()
        add_bag_ids_to_pre_wabo()
        
        logger.info('Importing wabo dossiers')
        import_wabo_dossiers()
        add_bag_ids_to_wabo()

    def handle(self, *args, **options):
        logger.info('Metadata import started')
        try:
            self.import_bag()
            self.import_dossiers()

        except Exception as e:
            raise Exception(
                "An exception occurred importing the metadata."
            ) from e