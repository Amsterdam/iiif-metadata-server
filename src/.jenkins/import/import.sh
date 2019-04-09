#!/bin/sh

set -e
set -u

DIR="$(dirname $0)"

dc() {
	docker-compose -p stadsarchief -f ${DIR}/docker-compose.yml $*
}

echo "Removing any previous backups"
rm -rf ${DIR}/backups
mkdir -p ${DIR}/backups

echo "Building dockers"
dc down
dc pull
dc build

echo "Starting and migrating db"
dc up -d database
dc run importer .jenkins/docker-wait.sh
dc run importer .jenkins/docker-migrate.sh

echo "Importing data"
dc run --rm importer

echo "Running backups"
dc exec -T database backup-db.sh stadsarchief

echo "Done"
