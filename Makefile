# This Makefile is based on the Makefile defined in the Python Best Practices repository:
# https://git.datapunt.amsterdam.nl/Datapunt/python-best-practices/blob/master/dependency_management/
#
# VERSION = 2020.01.29
.PHONY = help pip-tools install requirements update test init
dc = docker-compose

help:                               ## Show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

pip-tools:
	pip install pip-tools

install: pip-tools                  ## Install requirements and sync venv with expected state as defined in requirements.txt
	pip-sync requirements_dev.txt

requirements: pip-tools             ## Upgrade requirements (in requirements.in) to latest versions and compile requirements.txt
	pip-compile --upgrade --output-file requirements.txt requirements.in
	pip-compile --upgrade --output-file requirements_dev.txt requirements_dev.in

upgrade: requirements install       ## Run 'requirements' and 'install' targets

migrations:                         ## Make migrations
	$(dc) run --rm app python manage.py makemigrations

migrate:                            ## Migrate
	$(dc) run --rm app python manage.py migrate

build:                              ## Build docker image
	$(dc) build

push: build                         ## Push docker image to registry
	$(dc) push

push_semver:
	VERSION=$${VERSION} $(MAKE) push
	VERSION=$${VERSION%\.*} $(MAKE) push
	VERSION=$${VERSION%%\.*} $(MAKE) push

app:                                ## Run app
	$(dc) run --service-ports app

bash:                               ## Run the container and start bash
	$(dc) run --rm app bash

test:                               ## Execute tests
	$(dc) run --rm test pytest $(ARGS)
	$(dc) run --rm test flake8 --config=./flake8.cfg

clean:                              ## Clean docker stuff
	$(dc) down -v

env:                                ## Print current env
	env | sort

import_bag:                       ## Populate database with Bag data
	${dc} exec database update-table.sh bag_v11 bag_verblijfsobject public iiif_metadata_server
	${dc} exec database update-table.sh bag_v11 bag_ligplaats public iiif_metadata_server
	${dc} exec database update-table.sh bag_v11 bag_standplaats public iiif_metadata_server
	${dc} exec database update-table.sh bag_v11 bag_nummeraanduiding public iiif_metadata_server
	${dc} exec database update-table.sh bag_v11 bag_pand public iiif_metadata_server
	${dc} exec database update-table.sh bag_v11 bag_verblijfsobjectpandrelatie public iiif_metadata_server
	${dc} exec database update-table.sh bag_v11 bag_openbareruimte public iiif_metadata_server
	${dc} exec database psql -U postgres -c 'CREATE INDEX ON bag_nummeraanduiding(verblijfsobject_id)' iiif_metadata_server
