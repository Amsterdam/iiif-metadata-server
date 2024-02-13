import logging
import time

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from bag.constants import (BAG_TYPE_LIGPLAATS, BAG_TYPE_NUMMERAANDUIDING,
                           BAG_TYPE_OPENBARE_RUIMTE, BAG_TYPE_PAND,
                           BAG_TYPE_STANDPLAATS, BAG_TYPE_VERBLIJFSOBJECT)
from bag.exceptions import (BagIdException, IncorrectBagIdLengthException,
                            IncorrectGemeenteCodeException,
                            IncorrectObjectTypeException)
from bag.models import Ligplaats, Standplaats, Verblijfsobject

logger = logging.getLogger(__name__)


class BagHelper:
    @staticmethod
    def get_object_type_from_id(id):
        """
        Een landelijke identificatiecode bestaat uit 16 cijfers. De eerste 4 zijn gereserveerd voor
        de gemeentecode (0363 voor Amsterdam). De 2 cijfers daarna duiden een type BAG object aan:

        10 = een pand
        20 = een nummeraanduiding
        30 = een openbare ruimte
        01 = een verblijfsobject
        02 = een ligplaats
        03 = een standplaats
        (Zie wijken/constants.py)

        De laatste 10 cijfers zijn gereserveerd voor het volgnummer.

        Zie https://www.amsterdam.nl/stelselpedia/bag-index/catalogus-bag/landelijkid/

        :param id:
        :return: str
        """
        if not id:
            raise BagIdException("BAG id is empty")

        if len(id) != 16:
            raise IncorrectBagIdLengthException(
                f"Lengte van het landelijke id ({id}) is incorrect. "
                f"BAG ids hebben een lengte van 16"
            )

        gemeente_code = id[:4]
        if gemeente_code not in settings.GEMEENTE_CODE:
            raise IncorrectGemeenteCodeException(
                f"Ongeldige gemeentecode {gemeente_code} in landelijk id {id}. "
                f"Enkel de Amsterdamse gemeentecodes ({settings.GEMEENTE_CODE}) zijn toegestaan."
            )

        object_type = id[4:6]
        if object_type not in [
            BAG_TYPE_PAND,
            BAG_TYPE_NUMMERAANDUIDING,
            BAG_TYPE_OPENBARE_RUIMTE,
            BAG_TYPE_VERBLIJFSOBJECT,
            BAG_TYPE_LIGPLAATS,
            BAG_TYPE_STANDPLAATS,
        ]:
            raise IncorrectObjectTypeException(
                f"Objecttype {object_type} in landelijk id {id} is incorrect."
            )

        return object_type

    @staticmethod
    def get_object_from_id(id):
        object_type = BagHelper.get_object_type_from_id(id)
        if object_type == BAG_TYPE_VERBLIJFSOBJECT:
            bag_model = Verblijfsobject
        elif object_type == BAG_TYPE_LIGPLAATS:
            bag_model = Ligplaats
        elif object_type == BAG_TYPE_STANDPLAATS:
            bag_model = Standplaats
        else:
            raise IncorrectObjectTypeException(
                f"Objecttype {object_type} in landelijk id {id} is incorrect."
            )

        try:
            bag_object = (
                bag_model.objects.filter(id=id)
                .get()
            )
        except ObjectDoesNotExist:
            raise bag_model.DoesNotExist(
                f"{bag_model.__name__} met landelijk id {id} bestaat niet."
            )

        return bag_object


def retry(tries=3, delay=1, backoff=2):
    """Decorator to retry a function call a number of times"""

    def decorator(f):
        def wrapper(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 0:
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    logger.warning(
                        "Exception %s, retrying in %d seconds...", str(e), mdelay
                    )
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)

        return wrapper

    return decorator
