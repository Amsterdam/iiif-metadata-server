#!/usr/bin/env bash

set -u   # crash on missing env variables
set -e   # stop on any error
set -x   # print what we are doing

# Default credentials are for read-only access to the database.
# Migration needs write access, so overwrite the default credentials.
export DATABASE_HOST=${DATABASE_HOST_WRITE}
export DATABASE_USER=${DATABASE_USER_WRITE}
export DATABASE_PASSWORD=${DATABASE_PASSWORD_WRITE}
python manage.py migrate --noinput
