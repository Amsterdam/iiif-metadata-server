#!/usr/bin/env bash

set -u   # crash on missing env variables
set -e   # stop on any error
set -x   # print what we are doing

# Default credentials are for read-only access to the database.
# Migration needs write access, so overwrite the default credentials.
DATABASE_USER=${DATABASE_USER_WRITE}
DATABASE_PASSWORD=${DATABASE_PASSWORD_WRITE}

python manage.py migrate --noinput
