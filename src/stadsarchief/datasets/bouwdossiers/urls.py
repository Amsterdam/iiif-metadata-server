from rest_framework import routers
from stadsarchief.datasets.bouwdossiers import views as api_views


class BouwdossiersView(routers.APIRootView):
    """
    """


class BouwdossiersRouter(routers.DefaultRouter):
    APIRootView = BouwdossiersView


bouwdossiers = BouwdossiersRouter()

bouwdossiers.register(r'bouwdossier', api_views.BouwdossierViewSet,
                    base_name='bouwdossier')

urls = bouwdossiers.urls
