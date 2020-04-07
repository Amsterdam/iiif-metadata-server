import glob
import logging
import re

import xmltodict
from django.db import transaction, connection

from . import models

from stadsarchief.settings import DATA_DIR

log = logging.getLogger(__name__)

# This project now only uses the STADSDEEL codes received from the stadsarchief xml files.
# The decision was made to avoid confusion especially because the STADSDEEL
# codes are used in the document names.

# The below mapping was used earlier to map the STADSDEEl codes received from the stadsarchief xml files
# To the codes in bag api. It is kept for reference.

# Stadsarchief stadsdeel codes
# MAP_STADSDEEL_XML_CODE = {
#   'SA': 'Centrum',
#   'SU': 'Oost',
#   'SJ': 'West',
#   'SQ': 'Nieuw West',
#   'ST': 'Zuidoost',
#   'SN': 'Noord',
#   'SW': 'Zuid',
# }

# Bag stadsdeel codes
# MAP_STADSDEEL_NAAM_CODE = {
#   'Zuidoost': 'T',
#   'Centrum': 'A',
#   'Noord': 'N',
#   'Westpoort': 'B',
#   'West': 'E',
#   'Nieuw-West': 'F',
#   'Nieuw West': 'F',
#   'Zuid': 'K',
#   'Oost': 'M',
# }


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
    models.Document.objects.all().delete()
    models.Adres.objects.all().delete()
    models.BouwDossier.objects.all().delete()


def _normalize_bestand(bestand):
    bestand_parts = bestand.split('/')[-3:]
    if bestand_parts[1].isdigit():
        bestand_parts[1] = f"{int(bestand_parts[1]):05d}"
    else:
        log.warning(f"Invalid dossiernr in bestand {bestand}")
    return '/'.join(bestand_parts)


def openbaar_to_access(openbaar):
    if openbaar == 'J':
        return models.ACCESS_PUBLIC
    return models.ACCESS_RESTRICTED


def add_dossier(x_dossier, file_path, import_file, count, total_count):  # noqa C901
    dossiernr = x_dossier['dossierNr']
    titel = x_dossier['titel']
    if not titel:
        titel = ''
        log.warning(f"Missing titel for bouwdossier {dossiernr} in {file_path}")

    datering = get_datering(x_dossier.get('datering'))
    dossier_type = x_dossier.get('dossierType')
    stadsdeel = x_dossier.get('stadsdeelcode')

    if not stadsdeel:
        stadsdeel = ''
        log.warning(f"Missing stadsdeel for bouwdossier {dossiernr} in {file_path}")
    access = openbaar_to_access(x_dossier.get('openbaar'))

    bouwdossier = models.BouwDossier(
        importfile=import_file,
        dossiernr=dossiernr,
        stadsdeel=stadsdeel,
        titel=titel,
        datering=datering,
        dossier_type=dossier_type,
        access=access
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
            stadsdeel=stadsdeel,
            nummeraanduidingen=[],
            nummeraanduidingen_label=[],
            panden=[],
            verblijfsobjecten=[],
            verblijfsobjecten_label=[]
        )
        adres.save()

    for x_sub_dossier in get_list_items(x_dossier, 'subDossiers', 'subDossier'):
        titel = x_sub_dossier['titel']

        if not titel:
            titel = ''
            log.warning(f"Missing titel for subdossier for {bouwdossier.dossiernr} in {file_path}")

        subdossier_bestanden = get_list_items(x_sub_dossier, 'bestanden', 'url')

        # This is to check if there are any bestanden added to a subdossier directly. They are skipped because it is not
        # known if they are public or not
        if len(subdossier_bestanden) > 0:
            log.warning("bestanden in sub_dossier, unexpexted, no way to determine if this is Public or Restricted")
            log.warning(subdossier_bestanden)
            subdossier_bestanden = []

        # Documenten are now added with their public (access) flag. This way the serializer shows exactly which
        # group of bestanden (scans) are public or not.
        documenten = []
        for x_document in get_list_items(x_sub_dossier, 'documenten', 'document'):
            bestanden = get_list_items(x_document, 'bestanden', 'url')

            document = models.Document(
                barcode=x_document.get('barcode'),
                bouwdossier=bouwdossier,
                subdossier_titel=titel,
                bestanden=list(map(_normalize_bestand, bestanden)),
                access=openbaar_to_access(x_document.get('openbaar'))
            )

            documenten.append(document)

        models.Document.objects.bulk_create(documenten)

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

            # SAA_BWT_02.xml
            m = re.search('SAA_BWT_.\\w+\\.xml$', file_path)
            if m:
                with open(file_path) as fd:
                    xml = xmltodict.parse(fd.read())

                with transaction.atomic():
                    for x_dossier in get_list_items(xml, 'bwtDossiers', 'dossier'):
                        (count, total_count) = add_dossier(x_dossier, file_path, import_file, count,
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


def add_bag_ids():
    log.info("Add nummeraanduidingen")
    with connection.cursor() as cursor:
        cursor.execute("""
WITH adres_nummeraanduiding AS (
SELECT  sa.id AS id
      , ARRAY_AGG(bn.landelijk_id) AS nummeraanduidingen
      , ARRAY_AGG(_openbare_ruimte_naam || ' ' || huisnummer || huisletter ||
        CASE WHEN (huisnummer_toevoeging = '') IS NOT FALSE THEN '' ELSE '-' || huisnummer_toevoeging
        END) AS nummeraanduidingen_label
FROM stadsarchief_adres sa
JOIN bag_nummeraanduiding bn
ON sa.straat = bn._openbare_ruimte_naam
AND sa.huisnummer_van = bn.huisnummer
GROUP BY sa.id)
UPDATE stadsarchief_adres
SET nummeraanduidingen = adres_nummeraanduiding.nummeraanduidingen
  , nummeraanduidingen_label = adres_nummeraanduiding.nummeraanduidingen_label
FROM adres_nummeraanduiding
WHERE stadsarchief_adres.id = adres_nummeraanduiding.id
    """)
    log.info("Add panden")
    with connection.cursor() as cursor:
        cursor.execute("""
WITH adres_pand AS (
SELECT  sa.id
      , ARRAY_AGG(DISTINCT bp.landelijk_id) AS panden
      , ARRAY_AGG(DISTINCT bv.landelijk_id) AS vbos
      , ARRAY_AGG(bv._openbare_ruimte_naam || ' ' || bv._huisnummer || bv._huisletter ||
        CASE WHEN (bv._huisnummer_toevoeging = '') IS NOT FALSE THEN '' ELSE '-' || bv._huisnummer_toevoeging
        END) AS vbos_label
FROM stadsarchief_adres sa
JOIN bag_verblijfsobject bv ON sa.straat = bv._openbare_ruimte_naam
AND sa.huisnummer_van = bv._huisnummer
JOIN bag_verblijfsobjectpandrelatie bvbo ON bvbo.verblijfsobject_id = bv.id
JOIN bag_pand bp on bp.id = bvbo.pand_id
GROUP BY sa.id)
UPDATE stadsarchief_adres
SET panden = adres_pand.panden
  , verblijfsobjecten = adres_pand.vbos
  , verblijfsobjecten_label = adres_pand.vbos_label
FROM adres_pand
WHERE stadsarchief_adres.id = adres_pand.id
    """)

    # First we try to match with openbare ruimtes that are streets 01
    log.info("Add openbare ruimtes")
    with connection.cursor() as cursor:
        cursor.execute("""
UPDATE stadsarchief_adres sa
SET openbareruimte_id = opr.landelijk_id
FROM bag_openbareruimte opr
WHERE sa.straat = opr.naam
AND opr.vervallen = false
AND opr.type = '01'
        """)

    # If the openbareruimte was not yet found we try to match with other openbare ruimtes
    with connection.cursor() as cursor:
        cursor.execute("""
UPDATE stadsarchief_adres sa
SET openbareruimte_id = opr.landelijk_id
FROM bag_openbareruimte opr
WHERE sa.straat = opr.naam
AND (sa.openbareruimte_id IS NULL OR sa.openbareruimte_id = '')
        """)


def validate_import(min_bouwdossiers_count):
    with connection.cursor() as cursor:
        cursor.execute("""
SELECT COUNT(*)
  , array_length(panden, 1) IS NOT NULL AS has_panden
  , array_length(nummeraanduidingen, 1) IS NOT NULL AS has_nummeraanduidingen
  , openbareruimte_id IS NOT NULL AND openbareruimte_id <> '' AS has_openbareruimte_id
FROM stadsarchief_adres
GROUP BY has_openbareruimte_id, has_panden, has_nummeraanduidingen
        """)
        rows = cursor.fetchall()

        result = {
            'total': 0,
            'has_panden': 0,
            'has_nummeraanduidingen': 0,
            'has_openbareruimte_id': 0,
        }
        for row in rows:
            result['total'] += row[0]
            if row[1]:
                result['has_panden'] += row[0]
            if row[2]:
                result['has_nummeraanduidingen'] += row[0]
            if row[3]:
                result['has_openbareruimte_id'] += row[0]
    log.info('Validation import result: ' + str(result))

    assert result['total'] > min_bouwdossiers_count, \
        f'Imported total of {result["total"]} bouwdossiers is less than the required number {min_bouwdossiers_count}'
    assert result['has_panden'] > 0.8 * result['total']
    assert result['has_nummeraanduidingen'] > 0.8 * result['total']
    assert result['has_openbareruimte_id'] > 0.95 * result['total']
