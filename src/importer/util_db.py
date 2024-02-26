from django.db import connection
from django.apps import apps 


def get_app_model_names(model_name):
    app_models = apps.get_app_config(model_name).get_models()
    return [model._meta.db_table for model in app_models]

def truncate_tables(apps):
    models = [model for app in apps for model in get_app_model_names(app)]
    query = ""
    for model in models:
        query += f"""TRUNCATE TABLE {model} CASCADE;"""
    with connection.cursor() as cursor:
        cursor.execute(query)

def swap_tables_between_apps(app1, app2):
        importer_models = get_app_model_names(app1)
        bouwdossier_models = get_app_model_names(app2)

        query = ""
        for model in importer_models:
            new_model_name = model.replace(app1, app2)
            temp_model_name = model.replace(app1, 'temp')
            if (new_model_name not in bouwdossier_models):
                raise Exception(f"Model {model} of {app1} not found in {app2} app")
            
            query += f"""
ALTER TABLE {new_model_name} RENAME TO {temp_model_name};
ALTER TABLE {model} RENAME TO {new_model_name};
ALTER TABLE {temp_model_name} RENAME TO {model};"""
            
        with connection.cursor() as cursor:
            cursor.execute(query)