
#!/usr/bin/env bash

set -u   # crash on missing environment variables
set -e   # stop on any error
set -x   # log every command.

python manage.py run_import --delete --skip_validate_import --skipgetfiles --skipimport
