import re

from rest_framework.exceptions import APIException


class InvalidDossier(APIException):
    status_code = 400


def separate_dossier(dossier):
    """
    That separates the dossier combined with stadsdeel and dossiernr.
    If format is not correct, an APIException is raised
    """

    m = re.match(r"([A-Za-z]{2,4})_([A-Za-z0-9-]+)", dossier)

    # Check if dossier has correct format       
    if not m:
        raise InvalidDossier(
            f"The dossier {dossier} is not of the correct form. "
            "It should be defined in the form of 'AA_P123456' in which "
            "AA (or AAA or AAAA; a max of four characters) is the stadsdeel code and P123456 is the dossier number"
        )

    stadsdeel = m.group(1).upper()
    dossiernr = m.group(2)

    return stadsdeel, dossiernr