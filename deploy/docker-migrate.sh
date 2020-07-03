#!/usr/bin/env bash

set -u   # crash on missing env variables
set -e   # stop on any error
set -x   # print what we are doing

# When this script is called from Openstack deployment, the default credentials
# are for read-only access to the database. Migration needs write access, 
# so overwrite the default credentials.
if [ ! -z ${DATABASE_HOST_WRITE+x} ]; then
  export DATABASE_HOST=${DATABASE_HOST_WRITE}
  export DATABASE_USER=${DATABASE_USER_WRITE}
  export DATABASE_PASSWORD=${DATABASE_PASSWORD_WRITE}
fi

python manage.py migrate --noinput
