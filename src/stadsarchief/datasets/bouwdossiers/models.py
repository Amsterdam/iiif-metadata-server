from django.contrib.gis.db import models
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


class BouwDossier(models.Model):
    id = models.AutoField(primary_key=True)
    dossiernr = models.CharField(max_length=16, null=False, db_index=True)
    stadsdeel = models.CharField(max_length=3, db_index=True)
    titel = models.CharField(max_length=512, null=False, db_index=True)
    datering = models.CharField(max_length=4, null=True)  # jaartal
    dossier_type = models.CharField(max_length=64, null=True)
    dossier_status = models.CharField(max_length=1, null=True, choices=STATUS_CHOICES)
    access = models.CharField(max_length=1, null=True, choices=ACCESS_CHOICES)

    def __str__(self):
        return f'{self.dossiernr} - {self.titel}'

    class Meta:
        ordering = ('stadsdeel', 'dossiernr',)


class Adres(models.Model):
    id = models.AutoField(primary_key=True)
    bouwdossier = models.ForeignKey(BouwDossier,
                                    related_name='adressen',
                                    on_delete=CASCADE)
    straat = models.CharField(max_length=150)
    huisnummer_van = models.IntegerField()
    huisnummer_tot = models.IntegerField()
    openbareruimte_id = models.CharField(max_length=16, db_index=True)  # landelijk_id
    stadsdeel = models.CharField(max_length=3, db_index=True)  # stadsdeel code

    def __str__(self):
        return f'{self.straat} {self.huisnummer_van} - {self.huisnummer_tot}'


class SubDossier(models.Model):
    id = models.AutoField(primary_key=True)
    bouwdossier = models.ForeignKey(BouwDossier,
                                    related_name='subdossiers',
                                    on_delete=CASCADE)
    titel = models.CharField(max_length=128, null=False, db_index=True)
    access = models.CharField(max_length=1, null=True, choices=ACCESS_CHOICES)

    def __str__(self):
        return f'{self.titel}'


class Bestand(models.Model):
    id = models.AutoField(primary_key=True)
    subdossier = models.ForeignKey(SubDossier,
                                   related_name='bestanden',
                                   on_delete=CASCADE)
    dossier = models.ForeignKey(BouwDossier,
                                related_name='bestand',
                                on_delete=CASCADE)

    name = models.CharField(max_length=128, null=False)
    access = models.CharField(max_length=1, null=True, choices=ACCESS_CHOICES)

    def __str__(self):
        return self.name


class Nummeraanduiding(models.Model):
    id = models.AutoField(primary_key=True)
    adres = models.ForeignKey(Adres,
                              related_name='nummeraanduidingen',
                              on_delete=CASCADE)
    landelijk_id = models.CharField(max_length=16,  db_index=True)  # landelijk_id

    def __str__(self):
        return f'Nummeraanduiding {self.landelijk_id}'


class Pand(models.Model):
    id = models.AutoField(primary_key=True)
    adres = models.ForeignKey(Adres,
                              related_name='panden',
                              on_delete=CASCADE)
    landelijk_id = models.CharField(max_length=16, db_index=True)  # landelijk_id

    def __str__(self):
        return f'Pand {self.landelijk_id}'
