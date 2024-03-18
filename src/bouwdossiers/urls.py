from rest_framework import routers

from bouwdossiers import views as api_views


class BouwdossiersView(routers.APIRootView):
    """ """


class BouwdossiersRouter(routers.DefaultRouter):
    APIRootView = BouwdossiersView


bouwdossiers = BouwdossiersRouter()

bouwdossiers.register(
    r"bouwdossier", api_views.BouwDossierViewSet, basename="bouwdossier"
)

urls = bouwdossiers.urls
