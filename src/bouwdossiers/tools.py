import re

from rest_framework.exceptions import APIException


class InvalidDossier(APIException):
    status_code = 400


def separate_dossier(dossier):
    """
    That separates the dossier combined with stadsdeel and dossiernr.
    If format is not correct, an APIException is raised
    """

    pklist= dossier.upper().split('_')

    # Check if dossier has correct format       
    if len(pklist) != 2 or not re.match(r"^\D{2,4}$", pklist[0]):
        raise InvalidDossier(
            f"The dossier {dossier} is not of the correct form. "
            "It should be defined in the form of 'AA_P123456' in which "
            "AA (or AAA or AAAA; a max of four characters) is the stadsdeel code and P123456 is the dossier number"
        )

    stadsdeel, dossiernr = pklist[0], pklist[1]

    return stadsdeel, dossiernr