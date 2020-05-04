# Stadsarchief

Provide API and import for datasets from stadsarchief such as bouwdossiers


# Pre_wabo and wabo dossiers

wabo dossiers are dossiers after the law in 2008 came in to effect (https://wetten.overheid.nl/BWBR0024779/2018-07-28)
Dossiers before this law are called pre_wabo in the context of this repository.

It has been decided to import both kinds of dossiers in the same model (`BouwDossier`)
and add `source` field to differentiate between them.

The differences between pre_wabo and wabo are as follows:

- They reside in different cloud storage.
- The metadata for each are provided in different xml files.
- The xml files have slightly different structure thus are imported differently.
- WABO dossiers are not only bouwdossiers can also be other kinds. 
   (The model `BouwDossier` name may change in the future)


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
