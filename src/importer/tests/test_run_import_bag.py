import logging

import pytest
import vcr
from django.core.management import call_command

vcr_log = logging.getLogger("vcr")
vcr_log.setLevel(logging.WARNING)

my_vcr = vcr.VCR(
    serializer="yaml",
    cassette_library_dir="fixtures/cassettes",
    record_mode="new_episodes",
    match_on=["uri", "method"],
)


class TestBagImportBag:

    @my_vcr.use_cassette()
    @pytest.mark.django_db
    @pytest.mark.integration
    def test_import_bag_handle(self):
        call_command("run_import_bag")
