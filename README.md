# iiif-metadata-server

This project provides an import for metadata about Bouwdossiers from the Amsterdam Stadsarchief, and an API for the dataportaal frontend on https://data.amsterdam.nl/ to consume this metadata. The images described by this metadata are served by the [iiif-auth-proxy](https://github.com/Amsterdam/iiif-auth-proxy).


# Project architecture
This project follows the setup used in multiple projects and is described here: https://github.com/Amsterdam/opdrachten_team_dev.  


# Pre_wabo and wabo dossiers

wabo dossiers are dossiers which are granted after the WABO law ([Wet algemene bepalingen omgevingsrecht](https://wetten.overheid.nl/BWBR0024779/2023-04-19)) came in to effect around 2008.
Dossiers before this law are called pre_wabo in the context of this repository.

It has been decided to import both kinds of dossiers in the same model (`BouwDossier`)
and add `source` field to differentiate between them.

The differences between pre_wabo and wabo are as follows:

- They reside in different cloud storage for now. In the future, wabo dossiers wil be added to Stadsarchiefs Edepot
- The metadata for each are provided in different xml files.
- The xml files have slightly different structure thus are imported differently.
- WABO dossiers are not only bouwdossiers, but can also be other kinds. 
   (The model `BouwDossier` name may change in the future)


# Local development

Like for all applications in our team, the usual applies;

- `make dev` to run a local dev server
- `make test` to run the tests
