import logging
import os
from pathlib import Path

from azure.core.exceptions import ResourceExistsError
from django.conf import settings
from django.test import TestCase

from importer.util_azure import (
    get_blob_client,
    get_blob_container_client,
    get_container_client,
)

log = logging.getLogger(__name__)


def create_blob_container(container_name):
    blob_service_client = get_container_client()
    try:
        container_client = blob_service_client.create_container(
            container_name, public_access=None
        )
    except ResourceExistsError:
        pass
    container_client = blob_service_client.get_container_client(
        container=container_name
    )
    return container_client


def store_blob_in_container(container, file_path, filename):
    blob_client = get_blob_client(container, filename)
    with open(file=file_path, mode="rb") as data:
        blob_client.upload_blob(data, overwrite=True)
    return blob_client


class APITest(TestCase):

    @classmethod
    def setUpTestData(cls):
        create_blob_container(settings.AZURE_CONTAINER_NAME_BAG)

        dir_path = Path("importer/tests/data/bag")
        for file_path in os.listdir(dir_path):
            file = Path(dir_path, file_path)
            store_blob_in_container(settings.AZURE_CONTAINER_NAME_BAG, file, file.name)

    def test_retrieve_blob(self):
        client = get_blob_container_client(settings.AZURE_CONTAINER_NAME_BAG)
        names = [blob for blob in client.list_blob_names()]
        self.assertTrue(
            all(
                item in names
                for item in [
                    "bag_ligplaats.csv",
                    "bag_nummeraanduiding.csv",
                    "bag_openbareruimte.csv",
                    "bag_pand.csv",
                    "bag_standplaats.csv",
                    "bag_verblijfsobject.csv",
                    "bag_verblijfsobjectpandrelatie.csv",
                ]
            )
        )
