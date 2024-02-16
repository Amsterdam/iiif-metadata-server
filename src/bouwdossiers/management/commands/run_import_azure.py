import logging
import os
import shutil
import subprocess

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from django.conf import settings
from django.core.management import BaseCommand, call_command
from django.db import connection

from bouwdossiers.batch import (add_bag_ids_to_pre_wabo, add_bag_ids_to_wabo,
                                import_pre_wabo_dossiers, import_wabo_dossiers)

log = logging.getLogger(__name__)


BAG_FILE_NAME = 'bag_v11_latest.gz'
TABLES_TO_BE_IMPORTED = (
    'bag_verblijfsobject',
    'bag_ligplaats',
    'bag_standplaats',
    'bag_nummeraanduiding',
    'bag_pand',
    'bag_verblijfsobjectpandrelatie',
    'bag_openbareruimte'
)


def drop_all_tables():
    # Get all table names
    TABLE_NAMES_QUERY = "SELECT table_name " \
        "FROM information_schema.tables " \
        "WHERE table_schema = 'public' " \
        "AND table_type = 'BASE TABLE' " \
        "AND table_name != 'spatial_ref_sys';"

    cursor = connection.cursor()
    cursor.execute(TABLE_NAMES_QUERY)
    tables = cursor.fetchall()

    # Drop all tables
    with connection.cursor() as cursor:
        for table in tables:
            log.info(f"Dropping table {table[0]}")
            cursor.execute(f"DROP TABLE IF EXISTS {table[0]} CASCADE;")


def get_container_client(container_name):
    default_credential = DefaultAzureCredential()
    blob_service_client = BlobServiceClient(settings.STORAGE_ACCOUNT_URL, credential=default_credential)
    container_client = blob_service_client.get_container_client(container=container_name)
    return container_client


def download_bag_dump():
    log.info("Downloading BAG dump")
    container_client = get_container_client('bag')
    download_file_path = os.path.join('/tmp/', BAG_FILE_NAME)
    with open(file=download_file_path, mode="wb") as download_file:
        download_file.write(container_client.download_blob(BAG_FILE_NAME).readall())


def download_xml_files():
    if os.path.exists(settings.DATA_DIR):
        shutil.rmtree(settings.DATA_DIR)
    os.makedirs(settings.DATA_DIR)

    log.info("Downloading XML files")
    container_client = get_container_client('dossiers')
    blob_list = container_client.list_blobs()
    for blob in blob_list:
        log.info(f"Downloading {blob.name}")
        with open(f'{settings.DATA_DIR}{blob.name}', "wb") as xml_file:
            xml_file.write(container_client.download_blob(blob.name).readall())


def import_bag_dump():
    log.info("Importing BAG dump")
    db_user = settings.DATABASES['default']['USER']
    db_password = settings.DATABASES['default']['PASSWORD']
    db_name = settings.DATABASES['default']['NAME']

    for table in TABLES_TO_BE_IMPORTED:
        log.info("Importing table {table} from BAG dump")
        pg_restore_command = f"export PGPASSWORD={db_password} && " \
            f"pg_restore -U {db_user} -c --if-exists --no-acl --no-owner --table={table} " \
            f"--role ${db_name}_writer --schema=public /tmp/bag_v11_latest.gz -f /tmp/{table}_table.pg"
        subprocess.run(pg_restore_command, shell=True, check=True, capture_output=True, text=True)

        psql_command = f"export PGPASSWORD={db_password} && " \
                       f"psql -v ON_ERROR_STOP=1 -U {db_user} {db_name} < /tmp/{table}_table.pg"
        subprocess.run(psql_command, shell=True, check=True, capture_output=True, text=True)


class Command(BaseCommand):
    def handle(self, *args, **options):
        drop_all_tables()
        call_command('migrate')
        download_bag_dump()
        import_bag_dump()
        download_xml_files()

        import_pre_wabo_dossiers()
        add_bag_ids_to_pre_wabo()

        import_wabo_dossiers()
        add_bag_ids_to_wabo()

        # TODO: validate_import()
