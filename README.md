# Stadsarchief

Provide API and import for datasets from stadsarchief such as bouwdossiers


# Local development

Start database

`docker-compose up -d database
`

`cd src `

Migrate

`python manage.py migrate
`

Manual import


Before import BAG tables need to be loaded to be able to map BAG ids :

```
(cd .. && make import_bag)
```

Then we van run the import:

```
export BOUWDOSSIERS_OBJECTSTORE_PASSWORD=<get_from_rattic>
python manage.py run_import
```

Import only one file

`python manage.py run_import --max_files_count=1`

Skip downloads

`python manage.py run_import --skipgetfiles`


Run server

`python manage.py runserver`


Disable login requirement for local development

`Set 'ALWAYS_OK': LOCAL in DATAPUNT_AUTHZ`

Test API

`http://localhost:8000/stadsarchief/bouwdossier`

or

`http://localhost:8000/stadsarchief/docs/swagger`



# OpenAPI

Test API login in acceptance with SWAGGER :
 
`https://acc.api.data.amsterdam.nl/api/swagger/?url=/stadsarchief/docs/swagger.json`


# Import database from acceptance


docker-compose exec database update-db.sh stadsarchief <your username>
