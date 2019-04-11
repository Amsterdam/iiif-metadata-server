#!/usr/bin/env bash

set -u   # crash on missing environment variables
set -e   # stop on any error
set -x   # log every command.

source /.jenkins/docker-wait.sh

# load data in database
python manage.py migrate
python manage.py run_import
