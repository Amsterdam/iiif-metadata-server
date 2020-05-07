#!/bin/sh

set -e
set -u

DIR="$(dirname $0)"

dc() {
	docker-compose -p iiif-metadata-server -f ${DIR}/docker-compose.yml $*
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
dc run importer /deploy/wait-for-it.sh database:5432
dc run importer /deploy/docker-migrate.sh


# load latest bag into database
echo "Load latest verblijfsobjecten, ligplaatsen, standplaatsen, nummeraanduidingen en panden in iiif-metadata-server database"

# dc exec -T database update-db.sh atlas
dc exec -T database update-table.sh bag bag_verblijfsobject public iiif-metadata-server
dc exec -T database update-table.sh bag bag_ligplaats public iiif-metadata-server
dc exec -T database update-table.sh bag bag_standplaats public iiif-metadata-server
dc exec -T database update-table.sh bag bag_nummeraanduiding public iiif-metadata-server
dc exec -T database update-table.sh bag bag_pand public iiif-metadata-server
dc exec -T database update-table.sh bag bag_verblijfsobjectpandrelatie public iiif-metadata-server
dc exec -T database update-table.sh bag bag_openbareruimte public iiif-metadata-server


echo "Importing data"
dc run --rm importer

echo "Drop bag tables used for importing"
docker-compose -p iiif-metadata-server -f ${DIR}/docker-compose.yml exec -T database psql -U stadsarchief -c 'DROP TABLE bag_openbareruimte, bag_verblijfsobjectpandrelatie, bag_pand, bag_nummeraanduiding, bag_standplaats, bag_ligplaats, bag_verblijfsobject' stadsarchief

echo "Running backups"
dc exec -T database backup-db.sh iiif-metadata-server
dc down -v
echo "Done"
