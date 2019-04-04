from django.contrib.gis.db import models
from django.db.models import CASCADE

ACCESS_PUBLIC = 'P'
ACCESS_RESTRICTED = 'R'

ACCESS_CHOICES = (
    (ACCESS_PUBLIC, 'Public'),
    (ACCESS_RESTRICTED, 'Restricted')
)


class Bouwdossier(models.Model):
    id = models.AutoField(primary_key=True)
    dossiernr = models.CharField(max_length=16, null=False, db_index=True)
    titel = models.CharField(max_length=512, null=False, db_index=True)
    datering = models.CharField(max_length=4, null=True)  # jaartal
    access = models.CharField(max_length=1, null=True, choices=ACCESS_CHOICES)

    def __str__(self):
        return f'{self.dossiernr} - {self.titel}'

    class Meta:
        ordering = ('dossiernr',)


class Adres(models.Model):
    id = models.AutoField(primary_key=True)
    bouwdossier = models.ForeignKey(Bouwdossier,
                                    related_name='adres',
                                    on_delete=CASCADE)
    straat = models.CharField(max_length=150)
    huisnummer_van = models.IntegerField()
    huisnummer_tot = models.IntegerField()
    _openbareruimte = models.CharField(max_length=16, unique=True)  # landelijk_id
    _stadsdeel = models.CharField(max_length=3)  # stadsdeel code

    def __str__(self):
        return f'{self.straat} {self.huisnummer_van} - {self.huisnummer_tot}'


class SubDossier(models.Model):
    id = models.AutoField(primary_key=True)
    bouwdossier = models.ForeignKey(Bouwdossier,
                                    related_name='subdossier',
                                    on_delete=CASCADE)
    titel = models.CharField(max_length=128, null=False, db_index=True)
    access = models.CharField(max_length=1, null=True, choices=ACCESS_CHOICES)

    def __str__(self):
        return f'{self.titel}'


class Bestand(models.Model):
    id = models.AutoField(primary_key=True)
    subdossier = models.ForeignKey(SubDossier,
                                   related_name='bestand',
                                   on_delete=CASCADE)
    name = models.CharField(max_length=128, null=False)
    access = models.CharField(max_length=1, null=True, choices=ACCESS_CHOICES)

    def __str__(self):
        return self.name


class Nummeraanduiding(models.Model):
    id = models.AutoField(primary_key=True)
    adres = models.ForeignKey(Adres,
                              related_name='nummeraanduiding',
                              on_delete=CASCADE)
    landelijk_id = models.CharField(max_length=16, unique=True)  # landelijk_id

    def __str__(self):
        return f'Nummeraanduiding {self.landelijk_id}'


class Pand(models.Model):
    id = models.AutoField(primary_key=True)
    adres = models.ForeignKey(Adres,
                              related_name='pand',
                              on_delete=CASCADE)
    landelijk_id = models.CharField(max_length=16, unique=True)  # landelijk_id

    def __str__(self):
        return f'Pand {self.landelijk_id}'
