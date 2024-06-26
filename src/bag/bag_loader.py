import csv
import logging
import os
import subprocess
from zipfile import ZipFile

import requests
from django.conf import settings

from bag.utils import retry

logger = logging.getLogger(__name__)


class BagLoader:
    tmp_folder = "/tmp"

    tables = {
        "bag_ligplaats": "bag_ligplaatsen.csv.zip",
        "bag_openbareruimte": "bag_openbareruimtes.csv.zip",
        "bag_standplaats": "bag_standplaatsen.csv.zip",
        "bag_pand": "bag_panden.csv.zip",
        "bag_verblijfsobject": "bag_verblijfsobjecten.csv.zip",
        "bag_nummeraanduiding": "bag_nummeraanduidingen.csv.zip",
    }

    def _execute_psql_command(self, path, *, command, mode):
        database = settings.DATABASES["default"]
        command.extend(
            ["-h", database["HOST"], "-d", database["NAME"], "-U", database["USER"]]
        )
        try:
            kwargs = dict(
                check=True,
                env={"PGPASSWORD": str(database["PASSWORD"])},
            )
            with open(path, mode) as f:
                if mode == "r":
                    kwargs["stdin"] = f
                else:
                    kwargs["stdout"] = f
                subprocess.run(
                    command,
                    **kwargs,
                )
        except subprocess.CalledProcessError as e:
            logger.error(e.stderr)
            logger.exception(e)
            raise e

    def import_table_from_csv(self, *, table_name: str, path: str):
        """Import a table from a csv file"""
        with open(path, "r") as f:
            # Get column names in order
            header = f.readline()
        command = [
            "psql",
            "-c",
            f"COPY {table_name}({header}) FROM STDIN WITH "
            f"(FORMAT CSV, HEADER TRUE, DELIMITER ',', QUOTE '\"', ENCODING 'UTF8')",
        ]
        logger.info(f"Importing {table_name} into database")
        self._execute_psql_command(path, command=command, mode="r")

    def unpack_zip(self, *, table_name: str, endpoint: str):
        logger.info(f"Unpacking {table_name}")
        path_source = endpoint
        remove_file_ext = lambda x: x.rsplit(".", 1)[0]
        path_target = remove_file_ext(path_source)
        with ZipFile(path_source, "r") as zip:
            zip.extractall(
                path=os.path.dirname(path_target),
                members=[os.path.basename(path_target)],
            )
        return path_target

    def preprocess_csv_rows(self, reader: csv.DictReader, writer: csv.DictWriter):
        seen = {}
        for row in reader:
            key = row["Identificatie"]
            if key not in seen:
                seen[key] = row
            elif row["Volgnummer"] > seen[key]["Volgnummer"]:
                seen[key] = row

        filtered_rows = list(seen.values())
        writer.writeheader()
        for row in filtered_rows:
            writer.writerow(row)

    def preprocess_csv_files(self, csv_path_in, csv_path_out):
        with open(csv_path_in, "r") as infile, open(
            csv_path_out, "w", newline=""
        ) as outfile:
            reader = csv.DictReader(infile)
            writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
            self.preprocess_csv_rows(reader, writer)

    @retry(tries=5)
    def download_zip(self, *, table_name: str, endpoint: str, path_base: str):
        base_url = settings.BAG_CSV_BASE_URL
        url = f"{base_url}/{endpoint}"
        logger.info(f"Downloading {table_name} from {url}")
        response = requests.get(
            url,
            timeout=300,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        response.raise_for_status()
        path = f"{path_base}/{endpoint}"
        if os.path.exists(path):
            os.remove(path)
            logger.info(f"Zip {path} was removed")
        with open(path, "wb") as f:
            f.write(response.content)
        return path

    def load_tables_from_csv(self, csv_files):
        for table, path_csv in csv_files.items():
            self.import_table_from_csv(table_name=table, path=path_csv)
            logger.info(f"Table {table} was loaded")

    def import_tables_from_endpoint(self):
        csv_files = {}
        for table, endpoint in self.tables.items():
            logger.info(f"Loading table {table}")
            path_base = f"{self.tmp_folder}"
            path_zip = self.download_zip(
                table_name=table, endpoint=endpoint, path_base=path_base
            )
            path_csv = self.unpack_zip(table_name=table, endpoint=path_zip)
            path_csv_processed = f"{path_csv}-processed.csv"
            self.preprocess_csv_files(
                csv_path_in=path_csv, csv_path_out=path_csv_processed
            )
            csv_files[table] = path_csv_processed
        self.load_tables_from_csv(csv_files)
