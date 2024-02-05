import logging
import os
import shutil
import subprocess

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobClient, BlobServiceClient, ContainerClient
from django.conf import settings
from django.core.management import BaseCommand, call_command
from django.db import connection

from bouwdossiers.batch import (add_bag_ids_to_pre_wabo, add_bag_ids_to_wabo,
                                delete_all, import_pre_wabo_dossiers,
                                import_wabo_dossiers, validate_import)
from objectstore_utils import get_all_files

log = logging.getLogger(__name__)


def drop_all_tables():
    from django.db import connection

    # Get all table names
    cursor = connection.cursor()
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    tables = cursor.fetchall()

    # Drop all tables
    with connection.cursor() as cursor:
        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table[0]} CASCADE")

def get_container_client(container_name):
    account_url = "https://bouwdossiersdataoi5sk6et.blob.core.windows.net"
    default_credential = DefaultAzureCredential()
    blob_service_client = BlobServiceClient(account_url, credential=default_credential)
    container_client = blob_service_client.get_container_client(container=container_name) 
    return container_client


def download_bag_dump():
    from azure.identity import DefaultAzureCredential
    from azure.storage.blob import (BlobClient, BlobServiceClient,
                                    ContainerClient)

    container_client = get_container_client('bag') 

    FILE_NAME = 'bag_v11_latest.gz'
    download_file_path = '/tmp/' + FILE_NAME
    with open(file=download_file_path, mode="wb") as download_file: 
        download_file.write(container_client.download_blob(FILE_NAME).readall())


def download_xml_files():
    from azure.identity import DefaultAzureCredential
    from azure.storage.blob import (BlobClient, BlobServiceClient,
                                    ContainerClient)

    if os.path.exists(settings.DATA_DIR):
        shutil.rmtree(settings.DATA_DIR)
    os.makedirs(settings.DATA_DIR)

    container_client = get_container_client('dossiers') 
    blob_list = container_client.list_blobs()
    for blob in blob_list:
        print("\t" + blob.name)
        with open(f'{settings.DATA_DIR}{blob.name}', "wb") as xml_file:
            xml_file.write(container_client.download_blob(blob.name).readall())


def import_bag_dump():
    # pg_restore -U $POSTGRES_USER -c --if-exists --no-acl --no-owner --table=$2 --schema=$3 /tmp/$1_latest.gz > $2_table.pg
    # pg_restore -U postgres -c --if-exists --no-acl --no-owner --table=bag_verblijfsobject --schema=public /tmp/bag_v11_latest.gz > bag_verblijfsobject_table.pg

    TABLES_TO_BE_IMPORTED = (
        'bag_verblijfsobject',
        'bag_ligplaats',
        'bag_standplaats',
        'bag_nummeraanduiding',
        'bag_pand',
        'bag_verblijfsobjectpandrelatie',
        'bag_openbareruimte'
    )

    
    managed_identity = 'bouwdossiers-metadata-o'  # TODO: get this from settings

    for table in TABLES_TO_BE_IMPORTED:
        pg_restore_command = f"export PGPASSWORD={settings.DATABASE_PASSWORD} && " \
                            f"pg_restore -U {managed_identity} -c --if-exists --no-acl --no-owner --table={table} " \
                            f"--role ${settings.DATABASE_NAME}_writer --schema=public /tmp/bag_v11_latest.gz > {table}_table.pg"
        subprocess.run(pg_restore_command, shell=True, check=True, capture_output=True, text=True)
        
        psql_command = f"export PGPASSWORD={settings.DATABASE_PASSWORD} && " \
                       f"psql -v ON_ERROR_STOP=1 -U {managed_identity} {settings.DATABASE_NAME} < {table}_table.pg"
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
