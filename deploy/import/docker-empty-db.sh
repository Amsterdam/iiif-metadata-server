
#!/usr/bin/env bash

set -u   # crash on missing environment variables
set -e   # stop on any error
set -x   # log every command.

source /deploy/wait-for-it.sh database:5404

python manage.py run_import --delete --skip_validate_import --skipgetfiles --skipimport --skip_add_bag_ids
