import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.db import DatabaseError

try:
    # noinspection PyUnresolvedReferences
    from django.apps import apps
    get_model = apps.get_model
except ImportError:
    from django.db.models.loading import get_model

from django.http import HttpResponse

try:
    model = get_model(settings.HEALTH_MODEL)
except AttributeError:
    raise ImproperlyConfigured(
        'settings.HEALTH_MODEL {} doesn\'t resolve to '
        'a useable model'.format(settings.HEALTH_MODEL))


log = logging.getLogger(__name__)


def health(_request):
    """
    check database
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("select 1")
            assert cursor.fetchone()
    except DatabaseError:    # noqa
        log.exception("Database connectivity failed")
        return HttpResponse(
            "Database connectivity failed",
            content_type="text/plain", status=500)

    return HttpResponse(
        "Connectivity OK", content_type='text/plain', status=200)


def check_data(request):
    if model.objects.all().count() < 100:
        return HttpResponse(
            "Too few bouwdossiers data in the database",
            content_type="text/plain", status=500)

    return HttpResponse(
        "Data OK", content_type='text/plain', status=200)
