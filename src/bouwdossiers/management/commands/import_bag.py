import logging

from django.core.management.base import BaseCommand
from django.db import connection

from bag.bag_loader import BagLoader
from bag.koppeltabel_loader import KoppeltabelLoader

log = logging.getLogger(__name__)


class BagRetrievalError(Exception):
    pass

# TODO: Remove comments and split/extract into functions to improve readability
# TODO: Incorporate this into run_import
class Command(BaseCommand):
    help = "Create new schema and import BAG tables from datadienst export into new schema"

    def handle(self, *args, **options):
        bag = BagLoader()
        try:
            new_schema_name = "temp"
            
            # Create fresh new schema
            with connection.cursor() as cursor:
                cursor.execute(f"DROP SCHEMA IF EXISTS {new_schema_name} CASCADE;;")
                cursor.execute(f"CREATE SCHEMA {new_schema_name};")
            log.info(f'Schema "{new_schema_name}" created.')

            # Get a list of tables in the default schema
            tables = []
            with connection.cursor() as cursor:
                cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
                tables = [row[0] for row in cursor.fetchall()]

            # Create tables in the new schema with the same structure
            with connection.cursor() as cursor:
                for table in tables:
                   cursor.execute(f"CREATE TABLE {new_schema_name}.{table} (LIKE public.{table} INCLUDING ALL);")
            log.info(f"Duplicated tables into schema: {new_schema_name}")

            # Load bag into new schema
            with connection.schema_editor() as schema_editor:
                schema_editor.execute(f'SET search_path TO {new_schema_name};')
                bag.load_all_tables(new_schema_name)
                schema_editor.execute(f'SET search_path TO public;')
            
            # The link between Pand and Verblijfsobject is not available through the CSV API and needs to be
            # constructed manually for now
            koppeltabel = KoppeltabelLoader()
            koppeltabel.load()

        except Exception as e:
            raise Exception(
                "An exception occurred importing the BAG."
            ) from e
