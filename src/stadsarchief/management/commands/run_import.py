import logging

from django.core.management import BaseCommand
from stadsarchief.datasets.bouwdossiers.batch import import_bouwdossiers, delete_all
from stadsarchief.objectstore import get_all_files

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
            nargs=1,
            type=int,
            default=None,
            help='Maximum number of files to import')

    def handle(self, *args, **options):
        log.info('Stadsarchief import started')

        if not options['skipgetfiles']:
            log.info('Get files from objectstore')
            get_all_files()

        if options['delete']:
            log.info('Delete all data')
            delete_all()

        if not options['skipimport']:
            log.info('Import files')
            max_files_count = options['max_files_count'][0] if 'max_files_count' in options else None
            import_bouwdossiers(max_files_count)

        if not options['skip_add_bag_ids']:
            log.info('Add bag IDs')

        if not options['skip_validate_import']:
            log.info('Validate import')
