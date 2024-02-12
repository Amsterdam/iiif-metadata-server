import logging

from django.core.management.base import BaseCommand

from bag.bag_loader import BagLoader
from bag.koppeltabel_loader import KoppeltabelLoader

logger = logging.getLogger(__name__)


class BagRetrievalError(Exception):
    pass


class Command(BaseCommand):
    help = "Import BAG tables from datadienst export"

    def handle(self, *args, **options):
        bag = BagLoader()
        try:
            # To prevent incorrect data state, we restore our initial backup
            # if anything fails
            bag.truncate_bag_tables_cascade()
            bag.load_all_tables()

            # # The link between Pand and Verblijfsobject is not available through the CSV API and needs to be
            # # constructed manually
            koppeltabel = KoppeltabelLoader()
            koppeltabel.load()

        except Exception as e:
            raise Exception(
                "An exception occurred importing the BAG."
            ) from e
