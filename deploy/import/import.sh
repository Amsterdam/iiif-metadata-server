#!/bin/sh

set -u   # crash on missing env variables
set -e   # stop on any error
set -x   # print what we are doing

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
dc exec -T database update-table.sh bag_v11 bag_verblijfsobject public iiif_metadata_server
dc exec -T database update-table.sh bag_v11 bag_ligplaats public iiif_metadata_server
dc exec -T database update-table.sh bag_v11 bag_standplaats public iiif_metadata_server
dc exec -T database update-table.sh bag_v11 bag_nummeraanduiding public iiif_metadata_server
dc exec -T database update-table.sh bag_v11 bag_pand public iiif_metadata_server
dc exec -T database update-table.sh bag_v11 bag_verblijfsobjectpandrelatie public iiif_metadata_server
dc exec -T database update-table.sh bag_v11 bag_openbareruimte public iiif_metadata_server


echo "Importing data"
dc run --rm importer

#echo "Drop bag tables used for importing"
#docker-compose -p iiif-metadata-server -f ${DIR}/docker-compose.yml exec -T database psql -U iiif_metadata_server -c 'DROP TABLE bag_openbareruimte, bag_verblijfsobjectpandrelatie, bag_pand, bag_nummeraanduiding, bag_standplaats, bag_ligplaats, bag_verblijfsobject' iiif_metadata_server

echo "Running backups"
dc exec -T database backup-db.sh iiif_metadata_server
dc down -v
echo "Done"
