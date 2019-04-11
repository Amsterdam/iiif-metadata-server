import glob
import logging
import re

import xmltodict
from django.db import transaction

from . import models

from stadsarchief.settings import DATA_DIR

log = logging.getLogger(__name__)

MAP_STADSDEEL_NAAM_CODE = {
    'Zuidoost': 'T',
    'Centrum': 'A',
    'Noord': 'N',
    'Westpoort': 'B',
    'West': 'E',
    'Nieuw-West': 'F',
    'Zuid': 'K',
    'Oost': 'M',
}


def get_datering(value):
    result = None
    if value:
        if len(value) == 4:
            result = f"{value}-01-01"
        else:
            m = re.search("([0-9]{1,2})-([0-9]{4})", value)
            if m:
                result = f"{m.group(2)}-{m.group(1)}-01"
            else:
                log.warning(f"Unexpected datering pattern {value}")
                result = None
    return result


def get_list_items(d, key1, key2):
    x = d.get(key1)
    if x:
        items = x.get(key2)
        if items and not isinstance(items, list):
            items = [items]
        if items:
            return items
    return []


def delete_all():
    models.ImportFile.objects.all().delete()
    models.Pand.objects.all().delete()
    models.Nummeraanduiding.objects.all().delete()
    models.SubDossier.objects.all().delete()
    models.Adres.objects.all().delete()
    models.BouwDossier.objects.all().delete()


def add_dossier(x_dossier, file_path, stadsdeel_naam, import_file, count, total_count):
    dossiernr = x_dossier['dossierNr']
    stadsdeel = MAP_STADSDEEL_NAAM_CODE[stadsdeel_naam]
    titel = x_dossier['titel']
    if not titel:
        titel = ''
        log.warning(f"Missing titel for bouwdossier {dossiernr} in {file_path}")

    datering = get_datering(x_dossier.get('datering'))
    dossier_type = x_dossier.get('dossierType')

    bouwdossier = models.BouwDossier(
        importfile=import_file,
        dossiernr=dossiernr,
        stadsdeel=stadsdeel,
        titel=titel,
        datering=datering,
        dossier_type=dossier_type,
    )
    bouwdossier.save()
    count += 1
    total_count += 1

    if total_count % 1000 == 0:
        log.info(f"Bouwdossiers count in file: {count}, total: {total_count}")

    for x_adres in get_list_items(x_dossier, 'adressen', 'adres'):
        huisnummer_van = x_adres.get('huisnummerVan')
        huisnummer_van = int(huisnummer_van) if huisnummer_van else None
        huisnummer_tot = x_adres.get('huisnummerTot')
        huisnummer_tot = int(huisnummer_tot) if huisnummer_tot else None

        adres = models.Adres(
            bouwdossier=bouwdossier,
            straat=x_adres['straat'],
            huisnummer_van=huisnummer_van,
            huisnummer_tot=huisnummer_tot,
            stadsdeel=stadsdeel
        )
        adres.save()

    for x_sub_dossier in get_list_items(x_dossier, 'subDossiers', 'subDossier'):
        titel = x_sub_dossier['titel']

        if not titel:
            titel = ''
            log.warning(f"Missing titel for subdossier for {bouwdossier.dossiernr} in {file_path}")

        bestanden = get_list_items(x_sub_dossier, 'bestanden', 'bestand')

        sub_dossier = models.SubDossier(
            bouwdossier=bouwdossier,
            titel=titel,
            bestanden=bestanden
        )
        sub_dossier.save()

    return count, total_count


def import_bouwdossiers(max_file_count=None):  # noqa C901
    total_count = 0
    file_count = 0
    root_dir = DATA_DIR
    for file_path in glob.iglob(root_dir + '/**/*.xml', recursive=True):
        importfiles = models.ImportFile.objects.filter(name=file_path)
        if len(importfiles) > 0:
            # importfile = importfiles[0]
            continue

        import_file = models.ImportFile(name=file_path, status=models.IMPORT_BUSY)
        import_file.save()

        try:
            log.info(f"Processing - {file_path}")
            count = 0

            # SAA_BWT_Stadsdeel_Centrum_02.xml
            m = re.search('SAA_BWT_Stadsdeel_([^_]+)_\\d{1,5}\\.xml$', file_path)
            if m:
                stadsdeel_naam = m.group(1)
                with open(file_path) as fd:
                    xml = xmltodict.parse(fd.read())

                with transaction.atomic():
                    for x_dossier in get_list_items(xml, 'bwtDossiers', 'dossier'):
                        (count, total_count) = add_dossier(x_dossier, file_path, stadsdeel_naam, import_file, count,
                                                           total_count)

            import_file.status = models.IMPORT_FINISHED
            import_file.save()
            file_count += 1
            if max_file_count and file_count >= max_file_count:
                break

        except Exception as e:
            log.error(f"Error while processing file {file_path} : {e}")
            import_file.status = models.IMPORT_ERROR
            import_file.save()

    log.info(f"Import finished. Bouwdossiers total: {total_count}")
