import re

from rest_framework.exceptions import APIException


class InvalidDossier(APIException):
    status_code = 400


def separate_dossier(dossier):
    """
    That separates the dossier combined with stadsdeel and dossiernr.
    If format is not correct, an APIException is raised
    """

    dossier = dossier.replace('_', '')  # Also allow for searching by "SDC_1234"
    dossier = dossier.upper()  # Also allow to search by lower case letters

    try:
        # Check if dossier has correct format
        assert re.match(r'^\D{2,4}\d+$', dossier)
        # split the stadsdeel and dossier by using |
        stadsdeel, dossiernr = re.findall(r'\D{2,4}|\d+', dossier)
        return stadsdeel, dossiernr
    except AssertionError:
        raise InvalidDossier(
            f"The dossier {dossier} is not of the correct form. "
            "It should be defined in the form of 'AA123456' in which "
            "AA (or AAA or AAAA; a max of four characters) is the stadsdeel code and 123456 is the dossier number"
        )
