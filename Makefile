# This Makefile is based on the Makefile defined in the Python Best Practices repository:
# https://git.datapunt.amsterdam.nl/Datapunt/python-best-practices/blob/master/dependency_management/
#
# VERSION = 2020.01.29
.PHONY = help pip-tools install requirements update test init

UID:=$(shell id --user)
GID:=$(shell id --group)

dc = docker compose
run = $(dc) run --remove-orphans --rm -u ${UID}:${GID}
manage = $(run) dev python manage.py

help:                               ## Show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

pip-tools:
	pip install pip-tools

install: pip-tools                  ## Install requirements and sync venv with expected state as defined in requirements.txt
	pip-sync requirements_dev.txt

dev_requirements: pip-tools			## Create/update the dev requirements (in dev_requirements.in)
	pip-compile --upgrade --output-file requirements_dev.txt --allow-unsafe requirements_dev.in

linting_requirements: pip-tools		## Create/update the linting requirements (in linting_requirements.in)
	pip-compile --upgrade --output-file requirements_linting.txt --allow-unsafe requirements_linting.in

requirements: pip-tools linting_requirements dev_requirements			## Upgrade requirements (in requirements.in) to latest versions and compile requirements.txt
	pip-compile --upgrade --output-file requirements.txt --allow-unsafe requirements.in

upgrade: requirements install       ## Run 'requirements' and 'install' targets

migrations:                         ## Make migrations
	$(manage) makemigrations

migrate:                            ## Migrate
	$(manage) migrate

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

dev: migrate				        ## Run the development app (and run extra migrations first)
	$(run) --service-ports dev

bash:                               ## Run the container and start bash
	$(run) app bash

test:                               ## Execute tests
	$(run) test pytest $(ARGS)

lintfix:                            ## Execute lint fixes
	$(run) linting ruff check /app/ --fix
	$(run) linting ruff format /app/

lint:                               ## Execute lint checks
	$(run) linting ruff check /app/
	$(run) linting ruff format /app/ --check

clean:                              ## Clean docker stuff
	$(dc) down -v

env:                                ## Print current env
	env | sort

run_import:                       	## Populate database with new bag data and dossiers
	$(manage) run_import_bag $(ARGS)

trivy: 								## Detect image vulnerabilities
	$(dc) build app
	trivy image --ignore-unfixed docker-registry.data.amsterdam.nl/datapunt/iiif-metadata-server
