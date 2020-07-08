#!/usr/bin/env bash

set -u   # crash on missing environment variables
set -e   # stop on any error
set -x   # log every command.

# load data in database
python manage.py migrate
# Do full import. Delete all data

#if [ "$BOUWDOSSIERS_OBJECTSTORE_CONTAINER" = "dossiers_acceptance" ]
#then
python manage.py run_import --delete --skip_validate_import --skipimport
python manage.py run_import --skip_validate_import
python manage.py run_import --wabo --skip_validate_import
#else
#   python manage.py run_import --delete --skip_validate_import --skipimport
#   python manage.py run_import --min_bouwdossiers_count ${MIN_BOUWDOSSIERS_COUNT}
#   python manage.py run_import --wabo --min_bouwdossiers_count ${MIN_BOUWDOSSIERS_COUNT}
#fi
