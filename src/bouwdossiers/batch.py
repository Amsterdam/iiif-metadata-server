import glob
import logging
import re

import xmltodict
from django.conf import settings
from django.db import IntegrityError, connection, transaction

from . import models

log = logging.getLogger(__name__)

# This project now only uses the STADSDEEL codes received from the metadata xml files.
# The decision was made to avoid confusion especially because the STADSDEEL
# codes are used in the document names.

# The below mapping was used earlier to map the STADSDEEl codes received from the metadata xml files
# To the codes in bag api. It is kept for reference.

# stadsdeel codes
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
    bestand_parts = bestand.split('/')[4:]
    if bestand_parts[1].isdigit():
        bestand_parts[1] = f"{int(bestand_parts[1]):05d}"
    elif bestand_parts[2].isdigit():
        bestand_parts[2] = f"{int(bestand_parts[2]):05d}"
    else:
        log.warning(f"Invalid dossiernr in bestand {bestand}")
    return '/'.join(bestand_parts)


def openbaar_to_access(openbaar):
    if openbaar == 'J':
        return models.ACCESS_PUBLIC
    return models.ACCESS_RESTRICTED


def add_wabo_dossier(x_dossier, file_path, import_file, count, total_count):  # noqa C901
    """
    For information about wabo and pre_wabo please check the README
    Add wabo dossier to the the bouwdossier model. Structure of import is
    almost identical to pre_wabo xml to avoid confusion since only a few
    mappings are different and new fields are added.
    """
    dossier = x_dossier.get('intern_nummer')
    m = re.match(r"([a-z]+)_(?:([a-z]+)_)?(\d+)", dossier)
    if not m:
        log.error(f"Invalid intern_nummer {dossier} in {file_path}")
        return count, total_count

    stadsdeel = m.group(1)
    wabo_tag = m.group(2)
    dossiernr = m.group(3)

    if wabo_tag and wabo_tag == 'prewabo':
        stadsdeel += 'p'

    # There were titels longer than the allowed 512 characters, so to avoid errors we cut them off at 512
    titel = x_dossier.get('dossier_titel')[:509] + '...' if len(x_dossier.get('dossier_titel', '')) > 512 \
        else x_dossier.get('dossier_titel')

    if not titel:
        titel = ''
        log.warning(f"Missing titel for Wabo dossier {dossiernr} in {file_path}")

    datering = x_dossier.get('begindatum')
    dossier_type = x_dossier.get('omschrijving')
    if type(dossier_type) is str and len(dossier_type) > 255:
        dossier_type = dossier_type[:255]  # Cap at 255 characters

    olo_liaan_nummer = x_dossier.get('OLO_liaan_nummer')
    if type(olo_liaan_nummer) is str and len(olo_liaan_nummer):
        # In some cases the string starts with 'OLO'. We need to remove this
        olo_liaan_nummer = olo_liaan_nummer.replace('OLO', '')
    if not olo_liaan_nummer and wabo_tag == 'prewabo':
        olo_liaan_nummer = 0

    activiteiten = []
    for activiteit in get_list_items(x_dossier, 'activiteiten', 'activiteit'):
        activiteiten.append(activiteit[:250])
        if type(activiteit) is str and len(activiteit) > 250:
            log.warning(f'The activiteit str "{activiteit}" is more than 250 characters')

    bouwdossier = models.BouwDossier(
        importfile=import_file,
        dossiernr=dossiernr,
        stadsdeel=stadsdeel.upper(),  # Make it upper to follow the same format as pre_wabo dossiers
        titel=titel,
        datering=datering,
        dossier_type=dossier_type,
        olo_liaan_nummer=olo_liaan_nummer,
        wabo_bron=x_dossier.get('bron'),
        access=models.ACCESS_RESTRICTED,  # Until further notice, all wabo dossiers are restricted.
        source=models.SOURCE_WABO,
        activiteiten=activiteiten
    )

    try:
        with transaction.atomic():
            bouwdossier.save()
    except IntegrityError as e:
        log.error(f"Exception while saving {dossier} in {file_path} with : {e}")
        return count, total_count

    count += 1
    total_count += 1

    if total_count % 1000 == 0:
        log.info(f"Bouwdossiers count in file: {count}, total: {total_count}")

    for x_adres in get_list_items(x_dossier, 'locaties', 'locatie'):
        bag_id = x_adres.get('bag_id')
        panden = []
        verblijfsobjecten = []
        openbareruimte_id = None

        if bag_id:  # if no bag_ids, locatie aanduiding is available.
            panden.append(bag_id.get('pandidentificatie'))
            verblijfsobjecten.append(bag_id.get('verblijfsobjectidentificatie'))
            openbareruimte_id = bag_id.get('openbareruimteidentificatie')

        locatie_aanduiding = x_adres.get('locatie_aanduiding')
        if type(locatie_aanduiding) is str and len(locatie_aanduiding) > 250:
            locatie_aanduiding = locatie_aanduiding[:250]
            log.warning(f'The locatie_aanduiding str "{locatie_aanduiding}" is more than 250 characters')

        adres = models.Adres(
            bouwdossier=bouwdossier,
            straat=x_adres.get('straatnaam'),
            huisnummer_van=x_adres.get('huisnummer'),
            huisnummer_toevoeging=x_adres.get('huisnummertoevoeging'),
            huisnummer_letter=x_adres.get('huisletter'),
            stadsdeel=stadsdeel,
            nummeraanduidingen=[],
            nummeraanduidingen_label=[],
            openbareruimte_id=openbareruimte_id,
            panden=panden if panden else [],
            verblijfsobjecten=verblijfsobjecten if verblijfsobjecten else [],
            verblijfsobjecten_label=[],
            locatie_aanduiding=locatie_aanduiding
        )
        adres.save()

    documenten = []
    for x_document in get_list_items(x_dossier, 'documenten', 'document'):

        bestanden = []
        bestanden_pads = []
        for bestand in get_list_items(x_document, 'bestanden', 'bestand'):
            # Each bestand has an oorspronkelijk_pad.
            # oorspronkelijke_pads are added in another list (with the same order as bestanden)
            # to keep the same structure as the pre_wabo dossiers.
            # The removed part below is because we want to be consistent with the pre-wabo urls
            # in that we only store a relave url, not the full url
            bestand_str = bestand.get('URL').replace('https://conversiestraatwabo.amsterdam.nl/webDAV/', '')
            if type(bestand_str) is str and len(bestand_str) > 250:
                # Bestand urls longer than 250 characters are not supported by the DB. Since only one in about 200.000
                # records had this problem we'll just cap that url on 250 chars. This means that url will not work, but
                # we'll accept that for now.
                log.warning(f'The bestand str "{bestand_str}" is more than 250 characters')
                bestand_str = bestand_str[:250]
            bestanden.append(bestand_str)

            bestand_pad = bestand.get('oorspronkelijk_pad')
            if type(bestand_pad) is str and len(bestand_pad) > 250:
                # Bestand_pads longer than 250 characters are not supported by the DB. Since only one in about 200.000
                # records had this problem we'll just cap that pad on 250 chars. This means that pad will not work, but
                # we'll accept that for now.
                log.warning(f'The bestand_pad str "{bestand_pad}" is more than 250 characters')
                bestand_pad = bestand_pad[:250]
            bestanden_pads.append(bestand_pad)

        barcode = x_document.get('barcode')
        if not barcode and bestanden:
            # This is the case with wabo dossiers, and since wabo dossiers only have
            # one bestand per document, we use the number of the bestand as the barcode
            barcode = bestanden[0].split('/')[-1].split('.')[0]
            if type(barcode) is str and len(barcode) > 250:
                log.error(f'The barcode str "{barcode}" is more than 250 characters')

        document_omschrijving = x_document.get('document_omschrijving')
        if type(document_omschrijving) is str and len(document_omschrijving) > 250:
            document_omschrijving = document_omschrijving[:250]
            log.warning(f'The document_omschrijving str "{document_omschrijving}" is more than 250 characters')

        # Do not include metadata for paspoort scans. Een kavel paspoort is not a ID passport.
        if document_omschrijving and "paspoort" in document_omschrijving.lower() and "kavel" not in document_omschrijving.lower():
            continue

        document = models.Document(
            barcode=barcode,
            bouwdossier=bouwdossier,
            subdossier_titel=x_document.get('document_type'),
            oorspronkelijk_pad=bestanden_pads,
            bestanden=bestanden,
            access=models.ACCESS_RESTRICTED,
            document_omschrijving=document_omschrijving
        )

        documenten.append(document)

    if len(documenten) > 0:
        models.Document.objects.bulk_create(documenten)
    else:
        log.warning(f"No documenten for for {bouwdossier.dossiernr} in {file_path}")
    return count, total_count

def add_pre_wabo_dossier(x_dossier, file_path, import_file, count, total_count):  # noqa C901
    """
    For information about wabo and pre_wabo please check the README
    """
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

        if len(documenten) > 0:
            models.Document.objects.bulk_create(documenten)
        else:
            log.warning(f"No documenten for for {bouwdossier.dossiernr} in {file_path}")

    return count, total_count

def import_wabo_dossiers(max_file_count=None):  # noqa C901
    total_count = 0
    file_count = 0
    root_dir = settings.DATA_DIR
    for file_path in glob.iglob(root_dir + '/**/*.xml', recursive=True):
        wabo = re.search('WABO_.+\\.xml$', file_path)
        importfiles = models.ImportFile.objects.filter(name=file_path)

        if not wabo or len(importfiles) > 0:
            continue

        import_file = models.ImportFile(name=file_path, status=models.IMPORT_BUSY)
        import_file.save()

        try:
            log.info(f"Processing - {file_path}")
            count = 0

            #  This is temporarily fetched from the object store
            #  In the future, we will be pulling this from the client's webserver

            with open(file_path) as fd:
                xml = xmltodict.parse(fd.read())

            with transaction.atomic():
                for x_dossier in get_list_items(xml, 'dossiers', 'dossier'):
                    (count, total_count) = add_wabo_dossier(
                        x_dossier, file_path, import_file, count, total_count)

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

def import_pre_wabo_dossiers(max_file_count=None):  # noqa C901
    total_count = 0
    file_count = 0
    root_dir = settings.DATA_DIR
    for file_path in glob.iglob(root_dir + '/**/*.xml', recursive=True):
        # SAA_BWT_02.xml
        pre_wabo = re.search('SAA_BWT_.\\w+\\.xml$', file_path)
        importfiles = models.ImportFile.objects.filter(name=file_path)

        if not pre_wabo or len(importfiles) > 0:
            continue

        import_file = models.ImportFile(name=file_path, status=models.IMPORT_BUSY)
        import_file.save()

        try:
            log.info(f"Processing - {file_path}")
            count = 0

            with open(file_path) as fd:
                xml = xmltodict.parse(fd.read())

            with transaction.atomic():
                for x_dossier in get_list_items(xml, 'bwtDossiers', 'dossier'):
                    (count, total_count) = add_pre_wabo_dossier(
                        x_dossier, file_path, import_file, count, total_count)

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


def add_bag_ids_to_wabo():
    # This gets the nummeraanduidingen using the verblijfsobjecten instead of using the
    # address as it is done in the pre-wabo dossiers.
    log.info("Add nummeraanduidingen to wabo dossiers")
    with connection.cursor() as cursor:
        try:
            cursor.execute("""
WITH adres_nummeraanduiding AS (
    SELECT
        ba.id AS id,
        ARRAY_AGG(bag_nra.landelijk_id) AS nummeraanduidingen,
        ARRAY_AGG(bag_nra._openbare_ruimte_naam || ' ' || bag_nra.huisnummer || bag_nra.huisletter ||
            CASE WHEN (bag_nra.huisnummer_toevoeging = '') IS NOT FALSE THEN '' ELSE '-' || bag_nra.huisnummer_toevoeging
            END) AS nummeraanduidingen_label
    FROM bouwdossiers_adres ba
    JOIN bouwdossiers_bouwdossier bb ON bb.id = ba.bouwdossier_id
    JOIN bag_verblijfsobject bv ON bv.landelijk_id = any(ba.verblijfsobjecten)
    JOIN bag_nummeraanduiding bag_nra ON bag_nra.verblijfsobject_id = bv.id  -- bag_nra.verblijfsobject_id is het niet-landelijk verblijfsobjectid en daarom maken we de tussen-join mbv bag_verblijfsobject
    WHERE bb.source = 'WABO'
    GROUP BY ba.id)
UPDATE bouwdossiers_adres
SET nummeraanduidingen = adres_nummeraanduiding.nummeraanduidingen,
nummeraanduidingen_label = adres_nummeraanduiding.nummeraanduidingen_label
FROM adres_nummeraanduiding
WHERE bouwdossiers_adres.id = adres_nummeraanduiding.id
            """)
        except Exception:
            log.exception("An error occurred while adding the nummeraanduidingen.")
    log.info("Finished adding nummeraanduidingen to wabo dossiers")


def add_bag_ids_to_pre_wabo():
    log.info("Add nummeraanduidingen to pre-wabo dossiers")
    with connection.cursor() as cursor:
        cursor.execute("""
WITH adres_nummeraanduiding AS (
    SELECT
        ba.id AS id,
        ARRAY_AGG(bn.landelijk_id) AS nummeraanduidingen,
        ARRAY_AGG(_openbare_ruimte_naam || ' ' || huisnummer || huisletter ||
            CASE WHEN (bn.huisnummer_toevoeging = '') IS NOT FALSE THEN '' ELSE '-' || bn.huisnummer_toevoeging
            END) AS nummeraanduidingen_label
    FROM bouwdossiers_adres ba
    JOIN bouwdossiers_bouwdossier bb ON bb.id = ba.bouwdossier_id
    JOIN bag_nummeraanduiding bn
        ON ba.straat = bn._openbare_ruimte_naam
        AND ba.huisnummer_van = bn.huisnummer
    WHERE bb.source = 'EDEPOT'
    GROUP BY ba.id)
UPDATE bouwdossiers_adres
SET nummeraanduidingen = adres_nummeraanduiding.nummeraanduidingen,
nummeraanduidingen_label = adres_nummeraanduiding.nummeraanduidingen_label
FROM adres_nummeraanduiding
WHERE bouwdossiers_adres.id = adres_nummeraanduiding.id
        """)
    log.info("Finished adding nummeraanduidingen to pre-wabo dossiers")

    log.info("Add panden")
    with connection.cursor() as cursor:
        cursor.execute("""
WITH adres_pand AS (
    SELECT
        ba.id,
        ARRAY_AGG(DISTINCT bp.landelijk_id) AS panden,
        ARRAY_AGG(bv.landelijk_id) AS verblijfsobjecten,
        ARRAY_AGG(bv._openbare_ruimte_naam || ' ' || bv._huisnummer || bv._huisletter ||
            CASE WHEN (bv._huisnummer_toevoeging = '') IS NOT FALSE THEN '' ELSE '-' || bv._huisnummer_toevoeging
            END) AS verblijfsobjecten_label
    FROM bouwdossiers_adres ba
    JOIN bag_verblijfsobject bv ON ba.straat = bv._openbare_ruimte_naam
    AND ba.huisnummer_van = bv._huisnummer
    JOIN bag_verblijfsobjectpandrelatie bvbo ON bvbo.verblijfsobject_id = bv.id
    JOIN bag_pand bp on bp.id = bvbo.pand_id
    JOIN bouwdossiers_bouwdossier bb ON bb.id = ba.bouwdossier_id
    WHERE bb.source = 'EDEPOT'
    GROUP BY ba.id
)
UPDATE bouwdossiers_adres
SET panden = adres_pand.panden,
    verblijfsobjecten = adres_pand.verblijfsobjecten,
    verblijfsobjecten_label = adres_pand.verblijfsobjecten_label
FROM adres_pand
WHERE bouwdossiers_adres.id = adres_pand.id
        """)
    log.info("Finished adding panden")

    # First we try to match with openbare ruimtes that are streets 01
    log.info("Add openbare ruimtes")
    with connection.cursor() as cursor:
        cursor.execute("""
UPDATE bouwdossiers_adres ba
SET openbareruimte_id = opr.landelijk_id
FROM bag_openbareruimte opr
WHERE ba.straat = opr.naam
AND opr.vervallen = false
AND opr.type = '01'
        """)

    # If the openbareruimte was not yet found we try to match with other openbare ruimtes
    with connection.cursor() as cursor:
        cursor.execute("""
UPDATE bouwdossiers_adres ba
SET openbareruimte_id = opr.landelijk_id
FROM bag_openbareruimte opr
WHERE ba.straat = opr.naam
AND (ba.openbareruimte_id IS NULL OR ba.openbareruimte_id = '')
        """)
    log.info("Finished adding openbare ruimtes")


def validate_import(min_bouwdossiers_count):
    with connection.cursor() as cursor:
        cursor.execute("""
SELECT
    COUNT(*),
    array_length(panden, 1) IS NOT NULL AS has_panden,
    array_length(nummeraanduidingen, 1) IS NOT NULL AS has_nummeraanduidingen,
    openbareruimte_id IS NOT NULL AND openbareruimte_id <> '' AS has_openbareruimte_id
FROM bouwdossiers_adres
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

    log.info(
        f"{result['has_panden']} number of records of a total of {result['total']} records"
        f" ({result['has_panden'] / result['total'] * 100}%) has one or more panden."
        f" The required minimum is {0.8 * result['total']} (80%)."
    )
    assert result['total'] > min_bouwdossiers_count, \
        f'Imported total of {result["total"]} bouwdossiers is less than the required number {min_bouwdossiers_count}'
    assert result['has_panden'] > 0.8 * result['total'], \
        f"{result['has_panden']} number of records of a total of {result['total']} records " \
        f"({result['has_panden'] / result['total'] * 100}%) has one or more panden, " \
        f"which is less than the required minimum of {0.8 * result['total']} (80%)"
    assert result['has_nummeraanduidingen'] > 0.8 * result['total']
    assert result['has_openbareruimte_id'] > 0.95 * result['total']
