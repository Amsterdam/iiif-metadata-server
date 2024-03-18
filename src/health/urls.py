from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^health$", views.health),
    re_path(r"^data$", views.check_data),
]
