#!/usr/bin/env bash

set -u   # crash on missing environment variables
set -e   # stop on any error
set -x   # log every command.

# load data in database
python manage.py migrate
# Do full import. Delete all data

python manage.py run_import --delete --skip_validate_import --skipimport
python manage.py run_import --skip_validate_import
python manage.py run_import --wabo --skip_validate_import
