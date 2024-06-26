import logging
import os
import time
from calendar import timegm
from typing import List, Tuple

from django.conf import settings
from objectstore import get_full_container_list, objectstore

log = logging.getLogger(__name__)

DIR_CONTENT_TYPE = "application/directory"
DocumentList = List[Tuple[str, str]]


def get_objectstore_connection():
    assert os.getenv("BOUWDOSSIERS_OBJECTSTORE_PASSWORD")
    connection = objectstore.get_connection(settings.OBJECTSTORE)
    return connection


def get_all_files():
    connection = get_objectstore_connection()
    container_name = settings.BOUWDOSSIERS_OBJECTSTORE_CONTAINER
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    documents_meta = get_full_container_list(connection, container_name)
    for meta in documents_meta:
        if meta.get("content_type") != DIR_CONTENT_TYPE:
            name = meta.get("name")
            last_modified = meta.get("last_modified")
            dt = time.strptime(last_modified, "%Y-%m-%dT%H:%M:%S.%f")
            epoch_dt = timegm(dt)
            output_path = os.path.join(settings.DATA_DIR, name)
            dirname = os.path.dirname(output_path)
            os.makedirs(dirname, exist_ok=True)
            if os.path.isfile(output_path) and epoch_dt == os.path.getmtime(
                output_path
            ):
                log.info(f"Using cached file: {output_path}")
            else:
                log.info(f"Fetching file: {output_path}")
                new_data = connection.get_object(container_name, name)[1]
                with open(output_path, "wb") as file:
                    file.write(new_data)
                os.utime(output_path, (epoch_dt, epoch_dt))
