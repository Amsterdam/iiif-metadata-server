# This Makefile is based on the Makefile defined in the Python Best Practices repository:
# https://git.datapunt.amsterdam.nl/Datapunt/python-best-practices/blob/master/dependency_management/
#
# VERSION = 2020.01.29
.PHONY = help pip-tools install requirements update test init
dc = docker compose
run = $(dc) run --remove-orphans --rm
manage = $(run) dev python manage.py

help:                               ## Show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

pip-tools:
	pip install pip-tools

install: pip-tools                  ## Install requirements and sync venv with expected state as defined in requirements.txt
	pip-sync requirements_dev.txt

requirements: pip-tools             ## Upgrade requirements (in requirements.in) to latest versions and compile requirements.txt
	## The --allow-unsafe flag should be used and will become the default behaviour of pip-compile in the future
	## https://stackoverflow.com/questions/58843905
	pip-compile --upgrade --output-file requirements.txt --allow-unsafe requirements.in
	pip-compile --upgrade --output-file requirements_linting.txt --allow-unsafe requirements_linting.in
	pip-compile --upgrade --output-file requirements_dev.txt --allow-unsafe requirements_dev.in

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
	$(run) linting black /app/src/$(APP)
	$(run) linting autoflake /app/src --recursive --in-place --remove-unused-variables --remove-all-unused-imports --quiet
	$(run) linting isort /app/src/$(APP)

lint:                               ## Execute lint checks
	$(run) linting black --diff /app/src/$(APP)
	$(run) linting autoflake /app/src --check --recursive --quiet
	$(run) linting isort --diff --check /app/src/$(APP)

clean:                              ## Clean docker stuff
	$(dc) down -v

env:                                ## Print current env
	env | sort

run_import:                       	## Populate database with new bag data and dossiers
	$(manage) run_import_bag $(ARGS)

trivy: 								## Detect image vulnerabilities
	$(dc) build app
	trivy image --ignore-unfixed docker-registry.data.amsterdam.nl/datapunt/iiif-metadata-server
