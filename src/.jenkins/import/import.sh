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


# load latest bag into database
echo "Load latest verblijfsobjecten, ligplaatsen, standplaatsen, ummeraanduidingen en panden in stadsarchief database"

# dc exec -T database update-db.sh atlas
dc exec -T database update-table.sh bag bag_verblijfsobject public stadsarchief
dc exec -T database update-table.sh bag bag_ligplaats public stadsarchief
dc exec -T database update-table.sh bag bag_standplaats public stadsarchief
dc exec -T database update-table.sh bag bag_nummeraanduiding public stadsarchief
dc exec -T database update-table.sh bag bag_pand public stadsarchief
dc exec -T database update-table.sh bag bag_verblijfsobjectpandrelatie public stadsarchief
dc exec -T database update-table.sh bag bag_openbareruimte public stadsarchief


echo "Importing data"
dc run --rm importer

echo "Running backups"
dc exec -T database backup-db.sh stadsarchief

echo "Done"
