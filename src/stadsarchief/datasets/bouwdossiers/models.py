from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.db.models import CASCADE

ACCESS_PUBLIC = 'P'
ACCESS_RESTRICTED = 'R'

ACCESS_CHOICES = (
    (ACCESS_PUBLIC, 'Public'),
    (ACCESS_RESTRICTED, 'Restricted')
)

STATUS_AANVRAAG = 'A'
STATUS_BEHANDELING = 'B'

STATUS_CHOICES = (
    (STATUS_AANVRAAG, 'Aanvraag'),
    (STATUS_BEHANDELING, 'Behandeling')
)

IMPORT_BUSY = 'B'
IMPORT_FINISHED = 'F'
IMPORT_ERROR = 'E'

IMPORT_CHOICES = (
    (IMPORT_BUSY, 'Busy'),
    (IMPORT_FINISHED, 'Finished'),
    (IMPORT_ERROR, 'Error')
)


class ImportFile(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=512, null=False, unique=True)
    status = models.CharField(max_length=1, null=False, choices=IMPORT_CHOICES)
    last_import = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name}'

    class Meta:
        ordering = ('name',)


class BouwDossier(models.Model):
    id = models.AutoField(primary_key=True)
    importfile = models.ForeignKey(ImportFile,
                                   related_name='bouwdossiers',
                                   on_delete=CASCADE)
    dossiernr = models.CharField(max_length=16, null=False, db_index=True)
    stadsdeel = models.CharField(max_length=3, db_index=True)
    titel = models.CharField(max_length=512, null=False, db_index=True)
    datering = models.DateField(null=True)
    dossier_type = models.CharField(max_length=64, null=True)
    dossier_status = models.CharField(max_length=1, null=True, choices=STATUS_CHOICES)
    access = models.CharField(max_length=1, null=True, choices=ACCESS_CHOICES)

    def __str__(self):
        return f'{self.dossiernr} - {self.titel}'

    class Meta:
        ordering = ('stadsdeel', 'dossiernr',)


# TODO Do we need multiple adres instances for the same street and huisnummer van/tot
# ?? If there are multiple bouwdossiers for the same adres can we use the same adres instance ?
class Adres(models.Model):
    id = models.AutoField(primary_key=True)
    bouwdossier = models.ForeignKey(BouwDossier,
                                    related_name='adressen',
                                    on_delete=CASCADE)
    straat = models.CharField(max_length=150)
    huisnummer_van = models.IntegerField(null=True)
    huisnummer_tot = models.IntegerField(null=True)
    openbareruimte_id = models.CharField(max_length=16, db_index=True)  # landelijk_id
    stadsdeel = models.CharField(max_length=3, db_index=True)  # stadsdeel code
    nummeraanduidingen = ArrayField(models.CharField(max_length=16, null=False), blank=True)
    panden = ArrayField(models.CharField(max_length=16, null=False), blank=True)

    def __str__(self):
        return f'{self.straat} {self.huisnummer_van} - {self.huisnummer_tot}'

    class Meta:
        indexes = [GinIndex(fields=['nummeraanduidingen']), GinIndex(fields=['panden'])]


class SubDossier(models.Model):
    id = models.AutoField(primary_key=True)
    bouwdossier = models.ForeignKey(BouwDossier,
                                    related_name='subdossiers',
                                    on_delete=CASCADE)
    titel = models.CharField(max_length=128, null=False, db_index=True)
    bestanden = ArrayField(models.CharField(max_length=128, null=False), blank=True)
    access = models.CharField(max_length=1, null=True, choices=ACCESS_CHOICES)

    def __str__(self):
        return f'{self.titel}'
