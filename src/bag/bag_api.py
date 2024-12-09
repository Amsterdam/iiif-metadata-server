import logging
import os
from zipfile import ZipFile

import requests
from django.conf import settings
from toolz import partial, pipe

from bag.models import (
    Ligplaats,
    Nummeraanduiding,
    Openbareruimte,
    Pand,
    Standplaats,
    Verblijfsobject,
    Verblijfsobjectpandrelatie,
)
from bag.utils import read_csv, retry

logger = logging.getLogger(__name__)


class Zip:
    tmp_folder = "/tmp"
    model_to_endpoint = {
        Ligplaats: "bag_ligplaatsen.csv.zip",
        Openbareruimte: "bag_openbareruimtes.csv.zip",
        Standplaats: "bag_standplaatsen.csv.zip",
        Pand: "bag_panden.csv.zip",
        Verblijfsobject: "bag_verblijfsobjecten.csv.zip",
        Nummeraanduiding: "bag_nummeraanduidingen.csv.zip",
        Verblijfsobjectpandrelatie: "benkagg_bagpandbevatverblijfsobjecten.csv.zip",
    }

    @retry(tries=5)
    def download_zip(self, endpoint: str):
        api_endpoint = f"{settings.BAG_DUMP_BASE_URL}/{endpoint}"
        logger.info(f"Downloading from {api_endpoint}")
        response = requests.get(
            api_endpoint,
            timeout=300,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        response.raise_for_status()
        path = f"{self.tmp_folder}/{endpoint}"
        if os.path.exists(path):
            os.remove(path)
            logger.info(f"Existing zip {path} was removed")
        with open(path, "wb") as f:
            f.write(response.content)
        return path

    def unpack_zip(self, path_source: str):
        remove_file_ext = lambda x: x.rsplit(".", 1)[0]
        path_target = remove_file_ext(path_source)
        with ZipFile(path_source, "r") as zip:
            zip.extractall(
                path=os.path.dirname(path_target),
                members=[os.path.basename(path_target)],
            )
        return path_target

    def get_records(self, bag_model):
        assert (
            self.model_to_endpoint and bag_model in self.model_to_endpoint
        ), "No model_to_endpoints have been defined"

        return pipe(
            self.model_to_endpoint.get(bag_model),
            self.download_zip,
            self.unpack_zip,
            partial(read_csv, field_mapping=bag_model.get_column_field_mapping()),
        )
