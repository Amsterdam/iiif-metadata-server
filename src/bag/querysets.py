from django.db.models import QuerySet

from bag import constants


class VerblijfsobjectQuerySet(QuerySet):
    def met_woonfunctie(self):
        return self.filter(gebruiksdoel__icontains="woning")

    def is_zelfstandig(self):
        return self.exclude(gebruiksdoel_woonfunctie__icontains="onzelfst")

    def in_gebruik(self):
        return self.filter(status__icontains="in gebruik")

    def op_verdieping(self, verdieping):
        return self.filter(verdieping_toegang=verdieping)

    def in_panden(self, panden):
        return self.filter(panden__in=panden)


class PandQuerySet(QuerySet):
    def in_gebruik(self):
        return self.filter(status__icontains="in gebruik")

    def rij_rijtjeshuizen(self, rij):
        return self.filter(rijtjeshuis__rij=rij)


class NummeraanduidingQuerySet(QuerySet):
    def is_hoofdadres(self):
        return self.filter(type_adres__iexact=constants.ADRES_TYPE_HOOFDADRES)

    def verblijfsobjecten(self, verblijfsobjecten):
        return self.filter(verblijfsobject__in=verblijfsobjecten)
