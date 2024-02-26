import logging
import os
import shutil
from django.conf import settings

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

log = logging.getLogger(__name__)

# TODO: Make version to works locally
def get_container_client(container_name):
    default_credential = DefaultAzureCredential()
    blob_service_client = BlobServiceClient(settings.STORAGE_ACCOUNT_URL, credential=default_credential)
    container_client = blob_service_client.get_container_client(container=container_name)
    return container_client

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