# Copied from https://github.com/Amsterdam/drf_amsterdam

from collections import OrderedDict
from typing import Any

from django.db.models import Model
from rest_framework.fields import Field
from rest_framework.pagination import PageNumberPagination
from rest_framework.relations import RelatedField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.utils.urls import replace_query_param


class DisplayField(Field):
    """
    Add a `_display` field, based on Model string representation.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["source"] = "*"
        kwargs["read_only"] = True
        super().__init__(*args, **kwargs)

    def to_representation(self, value: Any) -> str:
        return str(value)


class HALPagination(PageNumberPagination):
    """
    Implement HAL-JSON style pagination.
    """

    page_size_query_param: str = "page_size"

    def get_paginated_response(self, data):
        assert self.request is not None

        self_link = self.request.build_absolute_uri()
        if self_link.endswith(".api"):
            self_link = self_link[:-4]

        assert self.page is not None

        if self.page.has_next():
            next_link = replace_query_param(
                self_link, self.page_query_param, self.page.next_page_number()
            )
        else:
            next_link = None

        if self.page.has_previous():
            prev_link = replace_query_param(
                self_link, self.page_query_param, self.page.previous_page_number()
            )
        else:
            prev_link = None

        return Response(
            OrderedDict(
                [
                    (
                        "_links",
                        OrderedDict(
                            [
                                ("self", dict(href=self_link)),
                                ("next", dict(href=next_link)),
                                ("previous", dict(href=prev_link)),
                            ]
                        ),
                    ),
                    ("count", self.page.paginator.count),
                    ("results", data),
                ]
            )
        )


class LinksField(RelatedField):
    lookup_field: str = "pk"
    lookup_url_kwarg: str
    view_name: str | None = None

    def __init__(self, view_name: str | None = None, **kwargs: Any):
        if view_name is not None:
            self.view_name = view_name
        assert self.view_name is not None, "The `view_name` argument is required."
        self.lookup_field = kwargs.pop("lookup_field", self.lookup_field)
        self.lookup_url_kwarg = kwargs.pop("lookup_url_kwarg", self.lookup_field)

        kwargs["read_only"] = True
        kwargs["source"] = "*"

        super().__init__(**kwargs)

    def get_url(
        self, obj: Model, view_name: str, request: Request | None, format: str | None
    ) -> str | None:
        """
        Given an object, return the URL that hyperlinks to the object.

        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """
        # Unsaved objects will not yet have a valid URL.
        if hasattr(obj, "pk") and obj.pk in (None, ""):
            return None

        lookup_value = getattr(obj, self.lookup_field)
        kwargs = {self.lookup_url_kwarg: lookup_value}

        return reverse(view_name, kwargs=kwargs, request=request, format=format)

    def to_representation(self, value: Any) -> dict[str, dict[str, str | None]]:
        request = self.context.get("request")
        assert self.view_name is not None

        return OrderedDict(
            [("self", {"href": self.get_url(value, self.view_name, request, None)})]
        )
