from rest_framework import routers
from .views import PublisherViewSet, PreparedPublisherViewSet


router = routers.DefaultRouter()
router.register(r'publishers', PublisherViewSet)

prepared_router = routers.DefaultRouter()
prepared_router.register(r'publishers', PreparedPublisherViewSet)
