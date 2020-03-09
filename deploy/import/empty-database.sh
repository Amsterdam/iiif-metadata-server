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

echo "Starting db"
dc up -d database
dc run importer /deploy/wait-for-it.sh

echo "Emptying db"
dc run --rm empty_db

echo "Running backups"
dc exec -T database backup-db.sh stadsarchief
dc down -v
echo "Done"
