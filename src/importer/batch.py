import glob
import json
import logging
import re

import xmltodict
from django.conf import settings
from django.db import IntegrityError, connection, transaction
from django.db.models import Case, Count, IntegerField, Q, Sum, When

import bouwdossiers.constants as const
from importer import models

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
#   'XY': 'Bodemdossiers',
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


def get_date_from_year(value):
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
    bestand_parts = bestand.split("/")[4:]
    if len(bestand_parts) < 3:
        log.error(f"Unexpected bestand : {bestand}")
        return None
    if bestand_parts[1].isdigit():
        bestand_parts[1] = f"{int(bestand_parts[1]):05d}"
    elif bestand_parts[2].isdigit():
        bestand_parts[2] = f"{int(bestand_parts[2]):05d}"
    return "/".join(bestand_parts)


def get_access(el):
    checks = {
        "openbaarheidsBeperking": ("N", "j"),
        "openbaar": ("J", "n"),
        "gevoelig_object": ("N", "j"),
        "bevat_persoonsgegevens": ("false", "true"),
    }

    if not any(el.get(check) for check in checks.keys()):
        return const.ACCESS_RESTRICTED

    for key, (default_value, expected_value) in checks.items():
        if el.get(key, default_value).lower() == expected_value:
            return const.ACCESS_RESTRICTED

    return const.ACCESS_PUBLIC


def openbaar_to_copyright(copyright):
    if copyright == "J":
        return const.COPYRIGHT_YES
    return const.COPYRIGHT_NO


def add_wabo_dossier(
    x_dossier, file_path, import_file, count, total_count, BWT_ids: json = None
):  # noqa C901
    """
    For information about wabo and pre_wabo please check the README
    Add wabo dossier to the the bouwdossier model. Structure of import is
    almost identical to pre_wabo xml to avoid confusion since only a few
    mappings are different and new fields are added.

    Originally this was for importing wabo dossiers. But now it is also
    used for prewabo dossiers that have the same XML structure as the
    wabo dossiers. This structure for files that originate from the 'tussenbestand'
    and are not archived in de edepot.
    """

    # The intern number can be something like sdz_prewabo_1274 or sdc_33
    # If prewabo is present it is a prewabo dossier.
    dossier = x_dossier.get("intern_nummer")
    m = re.match(r"([A-Za-z]+)_(?:([A-Za-z]+)_)?(.*[\d-]+)", dossier)
    if not m:
        log.error(f"Invalid intern_nummer {dossier} in {file_path}")
        return count, total_count

    stadsdeel = m.group(1)
    wabo_tag = m.group(2)
    dossiernr = m.group(3)

    if wabo_tag and wabo_tag == "prewabo":
        # prewabo key2 dossiers numbers can have the same values, for the same stadsdeel as existing
        # prewabo dossiers imported from the edepot. Therefore we add  the letter p to the stadsdeel
        # to make the combination unique.
        stadsdeel += "p"

    # There were titels longer than the allowed 512 characters, so to avoid errors we cut them off at 512
    titel = (
        x_dossier.get("dossier_titel")[:509] + "..."
        if len(x_dossier.get("dossier_titel", "")) > 512
        else x_dossier.get("dossier_titel")
    )

    if not titel:
        titel = ""
        log.warning(f"Missing titel for Wabo dossier {dossiernr} in {file_path}")

    bron = x_dossier.get("bron")
    _key = stadsdeel + "_" + dossiernr

    if bron == "BWT":
        "de BWT files hebben geen begindatum, omschrijving"
        datering = None
        dossier_type = ""

        # match with parameter jsonfile BWT_ids - bwt files have no get_access element in xml's
        _access = BWT_ids.get(_key, {}).get("dossier_access", const.ACCESS_RESTRICTED)

    else:
        datering = x_dossier.get("begindatum")
        dossier_type = (
            x_dossier.get("omschrijving").lower()
            if x_dossier.get("omschrijving")
            else None
        )
        if type(dossier_type) is str and len(dossier_type) > 255:
            dossier_type = dossier_type[:255]  # Cap at 255 characters

        _access = get_access(x_dossier)

    olo_liaan_nummer = x_dossier.get("OLO_liaan_nummer")
    if type(olo_liaan_nummer) is str and len(olo_liaan_nummer):
        # In some cases the string starts with Characters. We need to remove this
        olo_liaan_nummer = re.sub(r"^\D*", "", olo_liaan_nummer)
    # prewabo key2 dossiers and not all BWT-files have a olo number. Because we do not
    # want a None in the URL we set the olo number to 0
    if not olo_liaan_nummer and (wabo_tag == "prewabo" or bron == "BWT"):
        olo_liaan_nummer = 0

    activiteiten = []
    for activiteit in get_list_items(x_dossier, "activiteiten", "activiteit"):
        activiteiten.append(activiteit[:250])
        if type(activiteit) is str and len(activiteit) > 250:
            log.warning(
                f'The activiteit str "{activiteit}" is more than 250 characters'
            )

    bouwdossier = models.BouwDossier(
        importfile=import_file,
        dossiernr=dossiernr,
        stadsdeel=stadsdeel.upper(),  # Make it upper to follow the same format as pre_wabo dossiers
        titel=titel,
        datering=datering,
        dossier_type=dossier_type,
        olo_liaan_nummer=olo_liaan_nummer,
        wabo_bron=bron,
        access=_access,
        source=const.SOURCE_WABO,
        activiteiten=activiteiten,
    )

    # Save bouwdossier and try adding 'X' when double dossiernrs
    MAX_ATTEMPTS = 3
    success = False
    original_dossiernr = bouwdossier.dossiernr  # Store the original value

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with transaction.atomic():
                bouwdossier.save()
                success = True
                break
        except IntegrityError as e:
            if "duplicate key" in str(e).lower():
                log.warning(
                    f"Duplicate key error on attempt {attempt} for {dossier} in {file_path}: {e}"
                )
                bouwdossier.dossiernr = original_dossiernr + ("X" * attempt)
            else:
                log.error(
                    f"Non-retryable IntegrityError for {dossier} in {file_path}: {e}"
                )
                return count, total_count

    if not success:
        log.error(
            f"All {MAX_ATTEMPTS} save attempts failed for {dossier} in {file_path}"
        )
        return count, total_count

    count += 1
    total_count += 1

    if total_count % 1000 == 0:
        log.info(f"Bouwdossiers count in file: {count}, total: {total_count}")

    for x_adres in get_list_items(x_dossier, "locaties", "locatie"):
        bag_id = x_adres.get("bag_id")
        panden = []
        verblijfsobjecten = []
        openbareruimte_id = None
        nummeraanduidingen = []

        if bag_id:  # if no bag_ids, locatie aanduiding is available.
            panden.append(bag_id.get("pandidentificatie"))
            verblijfsobjecten.append(bag_id.get("verblijfsobjectidentificatie"))
            openbareruimte_id = bag_id.get("openbareruimteidentificatie")
            nummeraanduidingen.append(bag_id.get("Nummeraanduidingidentificatie"))

        elif (
            bron == "BWT"
        ):  # in bwt-files no bag_ids (locatie aanduiding?) in xml, match with parameter BWT_ids jsonfile
            _straat_huisnummer = (
                x_adres.get("straatnaam") + "_" + x_adres.get("huisnummer")
            )
            _adressen = BWT_ids.get(_key, {}).get("adressen", [])
            try:
                _result = [
                    item
                    for item in _adressen
                    if item.get("straat_huisnummer") == _straat_huisnummer.lower()
                ][0]

                [panden.append(item) for item in _result["panden"]]
                [
                    verblijfsobjecten.append(item)
                    for item in _result["verblijfsobjecten"]
                ]
                openbareruimte_id = _result["openbareruimte_id"]
                [
                    nummeraanduidingen.append(item)
                    for item in _result["nummeraanduidingen"]
                ]
            except:
                log.warning("straat_huisnummer niet gevonden in BWT bestand")

        locatie_aanduiding = x_adres.get("locatie_aanduiding")
        if type(locatie_aanduiding) is str and len(locatie_aanduiding) > 250:
            locatie_aanduiding = locatie_aanduiding[:250]
            log.warning(
                f'The locatie_aanduiding str "{locatie_aanduiding}" is more than 250 characters'
            )

        adres = models.Adres(
            bouwdossier=bouwdossier,
            straat=x_adres.get("straatnaam"),
            huisnummer_van=(
                x_adres.get("huisnummer").replace(",", "")
                if x_adres.get("huisnummer")
                else None
            ),
            huisnummer_toevoeging=x_adres.get("huisnummertoevoeging"),
            huisnummer_letter=x_adres.get("huisletter"),
            stadsdeel=stadsdeel,
            nummeraanduidingen=nummeraanduidingen,
            nummeraanduidingen_label=[],
            openbareruimte_id=openbareruimte_id,
            panden=panden,
            verblijfsobjecten=verblijfsobjecten if verblijfsobjecten else [],
            verblijfsobjecten_label=[],
            locatie_aanduiding=locatie_aanduiding,
        )
        adres.save()

    documenten = []
    for x_document in get_list_items(x_dossier, "documenten", "document"):

        bestanden = []
        bestanden_pads = []
        for bestand in get_list_items(x_document, "bestanden", "bestand"):
            # Each bestand has an oorspronkelijk_pad.
            # oorspronkelijke_pads are added in another list (with the same order as bestanden)
            # to keep the same structure as the pre_wabo dossiers.
            # The removed part below is because we want to be consistent with the pre-wabo urls
            # in that we only store a relative url, not the full url
            bestand_str = bestand.get("URL")
            for base_url in settings.WABO_BASE_URL:
                bestand_str = bestand_str.replace(base_url, "")

            ## the bestand_url from metadata is not what it should be, construct correctly here
            # catch the dossiertype from existence in bestand_str
            b = re.search(r"(SquitXO|KEY2|Decos|BWT)", bestand_str)
            if b:
                b_type = b.group(1)
                mapping = {
                    "KEY2": "Key2",
                    "SquitXO": "SquitXO",
                    "Decos": "Decos",
                    "BWT": "Decos",
                }
                bestand_type = mapping[b_type]

                _parts = bestand_str.split("/")

                if (
                    "BWT" in _parts[0]
                ):  # then it's from WABO/BWT and different url-format
                    _parts[0] = _parts[0].replace(" ", "/")
                    bestand_str = "/".join(_parts)
                else:  # place the file directly under dossier by removing folder before filename
                    _parts.pop(-2)
                    bestand_str = "/".join(_parts)
                    # add dossiertype after stadsdeel
                    bestand_str = re.sub(
                        rf"^{bouwdossier.stadsdeel}/",
                        f"{bouwdossier.stadsdeel}/{bestand_type}/",
                        bestand_str,
                    )

            if type(bestand_str) is str and len(bestand_str) > 250:
                # Bestand urls longer than 250 characters are not supported by the DB. Since only one in about 200.000
                # records had this problem we'll just cap that url on 250 chars. This means that url will not work, but
                # we'll accept that for now.
                log.warning(
                    f'The bestand str "{bestand_str}" is more than 250 characters'
                )
                bestand_str = bestand_str[:250]
            bestanden.append(bestand_str)

            bestand_pad = bestand.get("oorspronkelijk_pad")
            if type(bestand_pad) is str and len(bestand_pad) > 250:
                # Bestand_pads longer than 250 characters are not supported by the DB. Since only one in about 200.000
                # records had this problem we'll just cap that pad on 250 chars. This means that pad will not work, but
                # we'll accept that for now.
                log.warning(
                    f'The bestand_pad str "{bestand_pad}" is more than 250 characters'
                )
                bestand_pad = bestand_pad[:250]
            bestanden_pads.append(bestand_pad)

        barcode = x_document.get("barcode")
        if not barcode and bestanden:
            # This is the case with wabo dossiers, we use the name of the first bestand as the barcode
            barcode = bestanden[0].split("/")[-1].split(".")[0].split("_")[0]
            if type(barcode) is str:
                barcode = barcode.replace(" ", "%20")
            if type(barcode) is str and len(barcode) > 250:
                log.error(f'The barcode str "{barcode}" is more than 250 characters')

        document_omschrijving = x_document.get("document_omschrijving")
        if type(document_omschrijving) is str and len(document_omschrijving) > 250:
            document_omschrijving = document_omschrijving[:250]
            log.warning(
                f'The document_omschrijving str "{document_omschrijving}" is more than 250 characters'
            )

        # Do not include metadata for paspoort scans. Een kavel paspoort is not a ID passport.
        if (
            document_omschrijving
            and "paspoort" in document_omschrijving.lower()
            and "kavel" not in document_omschrijving.lower()
        ):
            continue

        # access document
        _access_doc = get_access(x_document)

        if bron == "BWT":
            # de BWT files zonder <bevat_persoonsgegevens> zijn openbaar als wel opgegeven die gebruiken
            # default bij ontbreken is ACCESS_RESTRICTED hier uitzondering voor BWT files.

            checks = [
                "openbaarheidsBeperking",
                "openbaar",
                "gevoelig_object",
                "bevat_persoonsgegevens",
            ]

            if not any(x_document.get(check) for check in checks):
                _access_doc = const.ACCESS_PUBLIC

        document = models.Document(
            barcode=barcode,
            bouwdossier=bouwdossier,
            subdossier_titel=x_document.get("document_type"),
            oorspronkelijk_pad=bestanden_pads,
            bestanden=bestanden,
            access=_access_doc,
            document_omschrijving=document_omschrijving,
        )

        documenten.append(document)

    if len(documenten) > 0:
        models.Document.objects.bulk_create(documenten)
    else:
        log.warning(f"No documenten for for {bouwdossier.dossiernr} in {file_path}")
    return count, total_count


def add_pre_wabo_dossier(
    x_dossier, file_path, import_file, count, total_count
):  # noqa C901
    """
    For information about wabo and pre_wabo please check the README
    """
    dossiernr = x_dossier["dossierNr"]
    titel = x_dossier["titel"]
    if not titel:
        titel = ""
        log.warning(f"Missing titel for bouwdossier {dossiernr} in {file_path}")

    datering = get_date_from_year(x_dossier.get("datering"))
    dossier_type = x_dossier.get("dossierType")
    gebruiksdoel = x_dossier.get("gebruiksdoel")
    bwt_nummer = x_dossier.get("bwtNummer")
    stadsdeel = x_dossier.get("stadsdeelcode")

    if not stadsdeel:
        stadsdeel = ""
        log.warning(f"Missing stadsdeel for bouwdossier {dossiernr} in {file_path}")
    access = get_access(x_dossier)
    access_restricted_until = get_date_from_year(
        x_dossier.get("openbaarheidsBeperkingTot")
    )

    bouwdossier = models.BouwDossier(
        importfile=import_file,
        dossiernr=dossiernr.zfill(5),
        stadsdeel=stadsdeel,
        titel=titel,
        datering=datering,
        dossier_type=dossier_type,
        gebruiksdoel=gebruiksdoel,
        bwt_nummer=bwt_nummer,
        access=access,
        access_restricted_until=access_restricted_until,
    )
    bouwdossier.save()
    count += 1
    total_count += 1

    if total_count % 1000 == 0:
        log.info(f"Bouwdossiers count in file: {count}, total: {total_count}")

    for x_adres in get_list_items(x_dossier, "adressen", "adres"):
        huisnummer_van = x_adres.get("huisnummerVan")
        huisnummer_van = int(huisnummer_van) if huisnummer_van else None
        huisnummer_tot = x_adres.get("huisnummerTot")
        huisnummer_tot = int(huisnummer_tot) if huisnummer_tot else None

        adres = models.Adres(
            bouwdossier=bouwdossier,
            straat=x_adres["straat"],
            huisnummer_van=huisnummer_van,
            huisnummer_tot=huisnummer_tot,
            stadsdeel=stadsdeel,
            nummeraanduidingen=[],
            nummeraanduidingen_label=[],
            panden=[],
            verblijfsobjecten=[],
            verblijfsobjecten_label=[],
        )
        adres.save()

    for x_sub_dossier in get_list_items(x_dossier, "subDossiers", "subDossier"):
        titel = x_sub_dossier["titel"]

        if not titel:
            titel = ""
            log.warning(
                f"Missing titel for subdossier for {bouwdossier.dossiernr} in {file_path}"
            )

        subdossier_bestanden = get_list_items(x_sub_dossier, "bestanden", "url")

        # This is to check if there are any bestanden added to a subdossier directly. They are skipped because it is not
        # known if they are public or not
        if len(subdossier_bestanden) > 0:
            log.warning(
                "bestanden in sub_dossier, unexpected, no way to determine if this is Public or Restricted"
            )
            log.warning(subdossier_bestanden)
            subdossier_bestanden = []

        # Documenten are now added with their public (access) flag. This way the serializer shows exactly which
        # group of bestanden (scans) are public or not.
        documenten = []
        for x_document in get_list_items(x_sub_dossier, "documenten", "document"):
            bestanden = get_list_items(x_document, "bestanden", "url")
            access = get_access(x_document)
            access_restricted_until = get_date_from_year(
                x_document.get("openbaarheidsBeperkingTot")
            )
            copyright = openbaar_to_copyright(x_document.get("auteursrechtBeperking"))
            copyright_until = get_date_from_year(
                x_document.get("auteursrechtBeperkingTot")
            )
            copyright_holders = x_document.get("auteursrechtHouders")
            copyright_manufacturers = x_document.get("auteursrechtVervaardigers")
            valid_bestanden = []
            for bestand in bestanden:
                normalized_bestand = _normalize_bestand(bestand)
                if normalized_bestand:
                    valid_bestanden.append(normalized_bestand)
            document = models.Document(
                barcode=x_document.get("barcode"),
                bouwdossier=bouwdossier,
                subdossier_titel=titel,
                bestanden=valid_bestanden,
                access=access,
                access_restricted_until=access_restricted_until,
                copyright=copyright,
                copyright_until=copyright_until,
                copyright_holders=copyright_holders,
                copyright_manufacturers=copyright_manufacturers,
            )

            documenten.append(document)

        if len(documenten) > 0:
            models.Document.objects.bulk_create(documenten)
        else:
            log.warning(f"No documenten for for {bouwdossier.dossiernr} in {file_path}")

    return count, total_count


def _read_btw_dossiers_verblijfsobjecten_ids(file_path) -> dict:
    log.info("read BTW wabo dossiers verblijfsobjecten_ids from json file")
    with open(file_path, "r") as file:
        data = json.load(file)
        return data


def _get_btw_verrijkings_bag_ids(root_dir) -> dict:
    try:
        BWT_filepath = root_dir + "/WABO/BWT_TMLO.json"
        BWT_ids = _read_btw_dossiers_verblijfsobjecten_ids(BWT_filepath)
        return BWT_ids
    except FileNotFoundError:
        log.error(
            f"Wabo-bwt bag_id verrijkingsfile staat niet op de juist plek: {BWT_filepath}"
        )


def import_wabo_dossiers(root_dir=settings.DATA_DIR, max_file_count=None):  # noqa C901
    total_count = 0
    file_count = 0

    BWT_ids = _get_btw_verrijkings_bag_ids(root_dir)

    for file_path in glob.iglob(root_dir + "/**/*.xml", recursive=True):
        wabo = re.search(r"/WABO/SD[A-Z]{1,2}( BWT)?/.+\.xml$|WABO_.+\.xml$", file_path)
        importfiles = models.ImportFile.objects.filter(name=file_path)

        if not wabo or len(importfiles) > 0:
            continue

        import_file = models.ImportFile(name=file_path, status=const.IMPORT_BUSY)
        import_file.save()

        try:
            log.info(f"Processing - {file_path}")
            count = 0

            #  This is temporarily fetched from the object store
            #  In the future, we will be pulling this from the client's webserver

            with open(file_path) as fd:
                xml = xmltodict.parse(fd.read())

            with transaction.atomic():
                for x_dossier in get_list_items(xml, "dossiers", "dossier"):
                    (count, total_count) = add_wabo_dossier(
                        x_dossier, file_path, import_file, count, total_count, BWT_ids
                    )

            import_file.status = const.IMPORT_FINISHED
            import_file.save()
            file_count += 1
            if max_file_count and file_count >= max_file_count:
                break

        except Exception as e:
            log.error(f"Error while processing file {file_path} : {e}")
            import_file.status = const.IMPORT_ERROR
            import_file.save()

    log.info(
        f"Import finished. Bouwdossiers total: {total_count}. Bouwdossiers count query: {models.BouwDossier.objects.count()}"
    )


def import_pre_wabo_dossiers(
    root_dir=settings.DATA_DIR, max_file_count=None
):  # noqa C901
    total_count = 0
    file_count = 0
    for file_path in glob.iglob(root_dir + "/**/*.xml", recursive=True):
        # SAA_BWT_02.xml
        pre_wabo = re.search(r"SAA_BWT_[A-Za-z-_0-9]+\.xml$", file_path)
        importfiles = models.ImportFile.objects.filter(name=file_path)

        if not pre_wabo or len(importfiles) > 0:
            continue

        import_file = models.ImportFile(name=file_path, status=const.IMPORT_BUSY)
        import_file.save()

        try:
            log.info(f"Processing - {file_path}")
            count = 0

            with open(file_path) as fd:
                xml = xmltodict.parse(fd.read())

            with transaction.atomic():
                for x_dossier in get_list_items(xml, "bwtDossiers", "dossier"):
                    (count, total_count) = add_pre_wabo_dossier(
                        x_dossier, file_path, import_file, count, total_count
                    )

            import_file.status = const.IMPORT_FINISHED
            import_file.save()
            file_count += 1
            if max_file_count and file_count >= max_file_count:
                break

        except Exception as e:
            log.error(f"Error while processing file {file_path} : {e}")
            import_file.status = const.IMPORT_ERROR
            import_file.save()

        log.info(
            f"Import in process. Imported files: {file_count}. Imported dossiers: {total_count}"
        )

    log.info(f"Import finished. Bouwdossiers total: {total_count}")


def add_bag_ids_to_wabo():
    # This gets the nummeraanduidingen using the verblijfsobjecten instead of using the
    # address as it is done in the pre-wabo dossiers.
    log.info("Add nummeraanduidingen to wabo dossiers")
    with connection.cursor() as cursor:
        try:
            cursor.execute(
                """
WITH adres_nummeraanduiding AS (
    SELECT
        ba.id AS id,
        ARRAY_AGG(bag_nra.identificatie) AS nummeraanduidingen,
        ARRAY_AGG(bag_opr.naam || ' ' || bag_nra.huisnummer ||
            CASE WHEN (bag_nra.huisletter = '') IS NOT FALSE THEN '' ELSE bag_nra.huisletter END ||
            CASE WHEN (bag_nra.huisnummertoevoeging = '') IS NOT FALSE THEN '' ELSE '-' || bag_nra.huisnummertoevoeging
            END) AS nummeraanduidingen_label
    FROM importer_adres ba
    JOIN importer_bouwdossier bb ON bb.id = ba.bouwdossier_id
    JOIN bag_nummeraanduiding bag_nra ON bag_nra.adresseertverblijfsobjectid = ANY(ba.verblijfsobjecten)
    JOIN bag_openbareruimte bag_opr ON bag_opr.identificatie = bag_nra.ligtaanopenbareruimteid
    WHERE bb.source = 'WABO'
    GROUP BY ba.id)
UPDATE importer_adres
SET nummeraanduidingen = adres_nummeraanduiding.nummeraanduidingen,
nummeraanduidingen_label = adres_nummeraanduiding.nummeraanduidingen_label
FROM adres_nummeraanduiding
WHERE importer_adres.id = adres_nummeraanduiding.id
            """
            )
        except Exception:
            log.exception("An error occurred while adding the nummeraanduidingen.")
    log.info("Finished adding nummeraanduidingen to wabo dossiers")


def add_bag_ids_to_pre_wabo():
    """
    This will try to add bag ids to addresses by matching streetname and house number.
    Currently all addresses in XML files are in Amsterdam. No residence is given in the XML file.
    Because Weesp is added to the bag we only use addresses in Amsterdam by
    adding the  *.id LIKE '0363%' clause.
    """
    # TODO check if there realy aren't Weesp adressen??
    log.info("Add nummeraanduidingen,verblijfsobjecten and panden to pre-wabo dossiers")
    with connection.cursor() as cursor:
        # Set parameter to disable parallel query. On Postgres docker
        # parallel query can fail due to lack of /dev/shm shared memory
        cursor.execute("SET max_parallel_workers_per_gather = 0")

        # In the importer_adres the adresses are given as a range
        # from huisnummer_van till huisnummer_tot
        # We want to include all nummeraanduidingen, verblijfsobjecten and panden in range
        # However, often  we can only use the even or odd number in the range when opposite
        # sides of the street use even resp odd numbers. But sometimes we have to use all the
        # numbers in the range. Therefore we use bouwblokken to select all numbers in the range
        # that also are in the same bouwblok as the start or the end of the range
        cursor.execute(
            """
WITH adres_start_end_bouwblok AS (
	SELECT iadre.id, ARRAY_AGG(DISTINCT bpand.ligtinbouwblokid) AS bouwblokken
		FROM importer_adres iadre
		JOIN bag_openbareruimte bopen ON bopen.naam = iadre.straat
		join bag_nummeraanduiding bnumm
			on bnumm.ligtaanopenbareruimteid = bopen.identificatie 
			and (bnumm.huisnummer = iadre.huisnummer_van 
		        or bnumm.huisnummer = iadre.huisnummer_tot)
			and bnumm.identificatie like '0363%' -- Only match Amsterdam addresses
		join bag_verblijfsobject bver on bver.identificatie = bnumm.adresseertverblijfsobjectid 
		join bag_verblijfsobjectpandrelatie bvpr on bvpr.verblijfsobjectenidentificatie = bver.identificatie
		join bag_pand bpand on bpand.identificatie = bvpr.ligtinpandenidentificatie
		JOIN importer_bouwdossier ibouw ON ibouw.id = iadre.bouwdossier_id
		where ibouw.source = 'EDEPOT'
		group by iadre.id
),
adres_pand AS (
    SELECT
	    iadre.id,
	    -- Then we  select all verblijfsobjecten and nummeraanduidingen in the range
        -- that also are in the same bouwblok as the start or end
        ARRAY_AGG(DISTINCT bpand.identificatie) AS panden,
        ARRAY_AGG(DISTINCT bverb.identificatie) AS verblijfsobjecten,
        ARRAY_AGG(DISTINCT bopen.naam || ' ' || bnumm.huisnummer || 
            CASE WHEN (bnumm.huisletter = '') IS NOT FALSE THEN '' ELSE bnumm.huisletter END ||
            CASE WHEN (bnumm.huisnummertoevoeging = '') IS NOT FALSE THEN '' ELSE '-' || bnumm.huisnummertoevoeging
            END) AS verblijfsobjecten_label,
        ARRAY_AGG(DISTINCT bnumm.identificatie) AS nummeraanduidingen,
        ARRAY_AGG(DISTINCT bopen.naam || ' ' || bnumm.huisnummer || 
            CASE WHEN (bnumm.huisletter = '') IS NOT FALSE THEN '' ELSE bnumm.huisletter END ||
            CASE WHEN (bnumm.huisnummertoevoeging = '') IS NOT FALSE THEN '' ELSE '-' || bnumm.huisnummertoevoeging
            END) AS nummeraanduidingen_label
	FROM importer_adres iadre
	JOIN bag_openbareruimte bopen ON bopen.naam = iadre.straat
	join bag_nummeraanduiding bnumm
		on bnumm.ligtaanopenbareruimteid = bopen.identificatie 
		and (bnumm.huisnummer >= iadre.huisnummer_van 
		    and bnumm.huisnummer <= iadre.huisnummer_tot)
		and bnumm.identificatie like '0363%' -- Only match Amsterdam addresses
	join bag_verblijfsobject bverb on bverb.identificatie = bnumm.adresseertverblijfsobjectid 
	join bag_verblijfsobjectpandrelatie bvpr on bvpr.verblijfsobjectenidentificatie = bverb.identificatie
	join bag_pand bpand on bpand.identificatie = bvpr.ligtinpandenidentificatie
	JOIN importer_bouwdossier ibouw ON ibouw.id = iadre.bouwdossier_id
	JOIN adres_start_end_bouwblok aseb ON aseb.id = iadre.id
    WHERE ibouw.source = 'EDEPOT'
    	AND bpand.ligtinbouwblokid=ANY(aseb.bouwblokken)
    GROUP BY iadre.id
)
UPDATE importer_adres
SET panden = adres_pand.panden,
    verblijfsobjecten = adres_pand.verblijfsobjecten,
    verblijfsobjecten_label = adres_pand.verblijfsobjecten_label,
    nummeraanduidingen = adres_pand.nummeraanduidingen,
    nummeraanduidingen_label = adres_pand.nummeraanduidingen_label
FROM adres_pand
WHERE importer_adres.id = adres_pand.id
        """
        )
    log.info(
        "Finished adding nummeraanduidingen, verblijfsobjecten and panden to pre-wabo dossiers"
    )

    # First we try to match with openbare ruimtes that are streets 01
    log.info("Add openbare ruimtes")
    with connection.cursor() as cursor:
        cursor.execute(
            """
UPDATE importer_adres iadre
SET openbareruimte_id = bopen.identificatie
FROM bag_openbareruimte bopen
WHERE iadre.straat = bopen.naam
AND (bopen.eindgeldigheid is NULL 
		OR bopen.eindgeldigheid >= NOW())
	AND bopen.typecode = '1'
	AND bopen.identificatie like '0363%' -- Only match Amsterdam streets
        """
        )

    # If the openbareruimte was not yet found we try to match with other openbare ruimtes
    with connection.cursor() as cursor:
        cursor.execute(
            """
UPDATE importer_adres iadre
SET openbareruimte_id = bopen.identificatie
FROM bag_openbareruimte bopen
WHERE iadre.straat = bopen.naam
AND bopen.identificatie LIKE '0363%'  -- Only match Amsterdam streets
AND (iadre.openbareruimte_id IS NULL OR iadre.openbareruimte_id = '')
        """
        )
    log.info("Finished adding openbare ruimtes")


def validate_import(min_bouwdossiers_count):

    result = models.Adres.objects.aggregate(
        total=Count("id"),
        has_panden=Sum(
            Case(
                When(panden__len__gt=0, then=1), default=0, output_field=IntegerField()
            )
        ),
        has_nummeraanduidingen=Sum(
            Case(
                When(nummeraanduidingen__len__gt=0, then=1),
                default=0,
                output_field=IntegerField(),
            )
        ),
        has_openbareruimte_id=Sum(
            Case(
                When(
                    ~Q(openbareruimte_id__isnull=True) & ~Q(openbareruimte_id=""),
                    then=1,
                ),
                default=0,
                output_field=IntegerField(),
            )
        ),
        wabo_total=Count("id", filter=Q(bouwdossier__source=const.SOURCE_WABO)),
        wabo_bwt=Count("id", filter=Q(bouwdossier__wabo_bron="BWT")),
        wabo_has_panden=Sum(
            Case(
                When(panden__len__gt=0, then=1), default=0, output_field=IntegerField()
            ),
            filter=Q(bouwdossier__source=const.SOURCE_WABO),
        ),
        wabo_has_nummeraanduidingen=Sum(
            Case(
                When(nummeraanduidingen__len__gt=0, then=1),
                default=0,
                output_field=IntegerField(),
            ),
            filter=Q(bouwdossier__source=const.SOURCE_WABO),
        ),
        wabo_has_openbareruimte_id=Sum(
            Case(
                When(
                    ~Q(openbareruimte_id__isnull=True) & ~Q(openbareruimte_id=""),
                    then=1,
                ),
                default=0,
                output_field=IntegerField(),
            ),
            filter=Q(bouwdossier__source=const.SOURCE_WABO),
        ),
        prewabo_total=Count("id", filter=Q(bouwdossier__source=const.SOURCE_EDEPOT)),
        prewabo_has_panden=Sum(
            Case(
                When(panden__len__gt=0, then=1), default=0, output_field=IntegerField()
            ),
            filter=Q(bouwdossier__source=const.SOURCE_EDEPOT),
        ),
        prewabo_has_nummeraanduidingen=Sum(
            Case(
                When(nummeraanduidingen__len__gt=0, then=1),
                default=0,
                output_field=IntegerField(),
            ),
            filter=Q(bouwdossier__source=const.SOURCE_EDEPOT),
        ),
        prewabo_has_openbareruimte_id=Sum(
            Case(
                When(
                    ~Q(openbareruimte_id__isnull=True) & ~Q(openbareruimte_id=""),
                    then=1,
                ),
                default=0,
                output_field=IntegerField(),
            ),
            filter=Q(bouwdossier__source=const.SOURCE_EDEPOT),
        ),
    )

    log.info("Validation import result: " + str(result))

    log.info(
        f"{result['has_panden']} number of records of a total of {result['total']} records"
        f" ({result['has_panden'] / result['total'] * 100}%) has one or more panden."
        f" The required minimum is {0.8 * result['total']} (80%)."
    )
    assert (
        result["total"] >= min_bouwdossiers_count
    ), f'Imported total of {result["total"]} bouwdossiers is less than the required number {min_bouwdossiers_count}'
    assert result["has_panden"] > 0.8 * result["total"], (
        f"{result['has_panden']} number of records of a total of {result['total']} records "
        f"({result['has_panden'] / result['total'] * 100}%) has one or more panden, "
        f"which is less than the required minimum of {0.8 * result['total']} (80%)"
    )
    assert result["has_nummeraanduidingen"] > 0.8 * result["total"]
    assert result["has_openbareruimte_id"] > 0.95 * result["total"]
