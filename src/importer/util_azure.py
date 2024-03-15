import logging
import os
import shutil
from django.conf import settings

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

log = logging.getLogger(__name__)

def get_container_client():
    if settings.AZURITE_STORAGE_CONNECTION_STRING:
        blob_service_client = BlobServiceClient.from_connection_string(settings.AZURITE_STORAGE_CONNECTION_STRING)
    else:
        default_credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(settings.STORAGE_ACCOUNT_URL, credential=default_credential)

    return blob_service_client

def get_blob_container_client(container_name):
    blob_service_client = get_container_client()
    container_client = blob_service_client.get_container_client(container=container_name)
    return container_client

def get_blob_client(container_name, blob_name):
    blob_service_client = get_container_client()
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    return blob_client

def download_blob_to_file(container_name, blob_name, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    blob_client = get_blob_client(container_name=container_name, blob_name=blob_name)
    file_path = f'{output_dir}/{blob_name}'
    with open(file_path, "wb") as file:
        blob = blob_client.download_blob().readall()
        file.write(blob)
    return file_path

def download_all_files_from_container(container_name, output_dir=settings.DATA_DIR):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    log.info(f"Downloading files from {container_name}")
    container_client = get_blob_container_client(container_name)
    blob_list = container_client.list_blobs()

    files = []
    for blob in blob_list:
        file_path = f'{output_dir}/{blob.name}'
        with open(f'{output_dir}/{blob.name}', "wb") as file:
            file.write(container_client.download_blob(blob.name).readall())
            files.append(file_path)
    return files

def remove_directory(dir):
    if os.path.exists(dir):
        shutil.rmtree(dir)