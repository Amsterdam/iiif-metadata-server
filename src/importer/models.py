from bouwdossiers.models import *
from django.db.models import CASCADE

class ImportFile(ImportFileBase):
    id = models.AutoField(primary_key=True)

class BouwDossier(BouwDossierBase):
    id = models.AutoField(primary_key=True)
    importfile = models.ForeignKey(ImportFile, related_name='bagimporter_bouwdossiers', on_delete=CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['stadsdeel', 'dossiernr'], name='unique_bagimporter_bouwdossier'),
        ]

class Adres(AdresBase):
    id = models.AutoField(primary_key=True)
    bouwdossier = models.ForeignKey(BouwDossier,
                                    related_name='bagimporter_adressen',
                                    on_delete=CASCADE)

class Document(DocumentBase):
    id = models.AutoField(primary_key=True)
    bouwdossier = models.ForeignKey(BouwDossier, related_name='bagimporter_documenten', on_delete=CASCADE)