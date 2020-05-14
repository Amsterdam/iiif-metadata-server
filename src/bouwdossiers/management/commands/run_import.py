import logging

from django.core.management import BaseCommand

from bouwdossiers.batch import (add_bag_ids, delete_all,
                                import_pre_wabo_dossiers, import_wabo_dossiers,
                                validate_import)
from objectstore_utils import get_all_files

log = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--skipgetfiles',
            action='store_true',
            dest='skipgetfiles',
            default=False,
            help='Skip getting files from objectstore')

        parser.add_argument(
            '--delete',
            action='store_true',
            dest='delete',
            default=False,
            help='Delete all data')

        parser.add_argument(
            '--skipimport',
            action='store_true',
            dest='skipimport',
            default=False,
            help='Skip import data from files')

        parser.add_argument(
            '--skip_add_bag_ids',
            action='store_true',
            dest='skip_add_bag_ids',
            default=False,
            help='Add bag ids to bouwdossiers')

        parser.add_argument(
            '--skip_validate_import',
            action='store_true',
            dest='skip_validate_import',
            default=False,
            help='Skip validate import')

        parser.add_argument(
            '--max_files_count',
            # action='store_true',
            dest='max_files_count',
            type=int,
            default=None,
            help='Maximum number of files to import')

        parser.add_argument(
            '--min_bouwdossiers_count',
            # action='store_true',
            dest='min_bouwdossiers_count',
            type=int,
            default=10000,
            help='Minimum amount of bouwdossiers to be added')

        parser.add_argument(
            '--wabo',
            action='store_true',
            dest='wabo',
            default=False,
            help='import wabo dossiers')

    def import_dossiers(self, options):
        max_files_count = options['max_files_count']

        if options['wabo']:
            log.info('Import wabo files')
            import_wabo_dossiers(max_files_count)
        else:
            log.info('Import pre wabo files')
            import_pre_wabo_dossiers(max_files_count)

    def handle(self, *args, **options):
        log.info('Metadata import started')

        if not options['skipgetfiles']:
            log.info('Get files from objectstore')
            get_all_files()

        if options['delete']:
            log.info('Delete all data')
            delete_all()

        if not options['skipimport']:
            self.import_dossiers(options)

        if not options['skip_add_bag_ids']:
            log.info('Add bag IDs')
            add_bag_ids()

        if not options['skip_validate_import']:
            log.info('Validate import')
            validate_import(options['min_bouwdossiers_count'])
