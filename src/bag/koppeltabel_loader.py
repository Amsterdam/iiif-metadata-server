import logging

import requests
from django.conf import settings

from .models import Verblijfsobjectpandrelatie
from .utils import retry

logger = logging.getLogger(__name__)


class KoppeltabelLoader:
    endpoint = "/v1/bag/verblijfsobjecten/"

    def load(self):
        verblijfsobjecten = self.download()
        records = self.get_records(verblijfsobjecten)
        self.load_records_in_batches(records)
        logger.info("Loaded %s records into koppeltabel", len(records))

    def download(self):
        """Download the data from the endpoint"""
        logger.info(f"Downloading data from {self.endpoint}")
        url = settings.DATADIENSTEN_API_BASE_URL + self.endpoint
        verblijfsobjecten = []
        page = 1
        while page:
            response = self._make_request(page, url)
            verblijfsobjecten.extend(response["_embedded"]["verblijfsobjecten"])
            next = response["_links"].get("next", {})
            if next:
                page += 1
            else:
                page = None
        return verblijfsobjecten

    def get_records(self, verblijfsobjecten):
        logger.info("Constructing records")
        records = []
        for vot in verblijfsobjecten:
            for pand in vot["_links"]["ligtInPanden"]:
                records.append(
                    dict(
                        verblijfsobject_id=vot["identificatie"],
                        pand_id=pand["identificatie"],
                    )
                )
        return records

    def load_records_in_batches(self, records, batch_size=1000):
        """
        Load data into Verblijfsobjectpandrelatie with bulk imports
        Split into batches
        """
        for i in range(0, len(records), batch_size):
            Verblijfsobjectpandrelatie.objects.bulk_create(
                Verblijfsobjectpandrelatie(**record)
                for record in records[i : i + batch_size]
            )

    @retry()  # The endpoint is sometimes unstable and needs retries
    def _make_request(self, page, url):
        params = {
            "_pageSize": 5000,
            "_fields": ",".join(["identificatie", "ligtInPanden"]),
            "page": page,
        }
        logger.info(f"Downloading {url} page {page}", extra=params)
        response = requests.get(url, timeout=720, params=params)
        response.raise_for_status()
        return response.json()
