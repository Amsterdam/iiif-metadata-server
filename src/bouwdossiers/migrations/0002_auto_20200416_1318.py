# Generated by Django 2.2.12 on 2020-04-16 13:18

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bouwdossiers", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="adres",
            name="huisnummer_letter",
            field=models.CharField(default=None, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name="adres",
            name="huisnummer_toevoeging",
            field=models.CharField(default=None, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name="adres",
            name="locatie_aanduiding",
            field=models.CharField(max_length=250, null=True),
        ),
        migrations.AddField(
            model_name="bouwdossier",
            name="olo_liaan_nummer",
            field=models.IntegerField(default=None, null=True),
        ),
        migrations.AddField(
            model_name="bouwdossier",
            name="wabo_bron",
            field=models.CharField(default=None, max_length=30, null=True),
        ),
        migrations.AddField(
            model_name="document",
            name="document_type",
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AddField(
            model_name="document",
            name="oorspronkelijk_pad",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=250),
                blank=True,
                default=list,
                size=None,
            ),
        ),
        migrations.AlterField(
            model_name="adres",
            name="openbareruimte_id",
            field=models.CharField(db_index=True, max_length=16, null=True),
        ),
        migrations.AlterField(
            model_name="adres",
            name="straat",
            field=models.CharField(max_length=150, null=True),
        ),
        migrations.AlterField(
            model_name="document",
            name="barcode",
            field=models.CharField(db_index=True, max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name="document",
            name="bestanden",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=250), blank=True, size=None
            ),
        ),
        migrations.AlterField(
            model_name="document",
            name="subdossier_titel",
            field=models.TextField(blank=True, null=True),
        ),
    ]
