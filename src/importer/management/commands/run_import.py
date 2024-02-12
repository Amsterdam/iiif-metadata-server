import logging

from django.core.management.base import BaseCommand
from django.db import connection
import bouwdossiers.models as bd_models

from importer.batch import (add_bag_ids_to_pre_wabo,
                            add_bag_ids_to_wabo,
                            import_wabo_dossiers, 
                            import_pre_wabo_dossiers)


logger = logging.getLogger(__name__)


class BagRetrievalError(Exception):
    pass


class Command(BaseCommand):
    help = "Import BAG tables from datadienst export"

    def handle(self, *args, **options):
        try:
            import_pre_wabo_dossiers()
            add_bag_ids_to_pre_wabo()
            
            import_wabo_dossiers()
            add_bag_ids_to_wabo()

        except Exception as e:
            raise Exception(
                "An exception occurred duplicating the db tables."
            ) from e