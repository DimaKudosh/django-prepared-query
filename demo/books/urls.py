from rest_framework import routers
from .views import PublisherViewSet


router = routers.DefaultRouter()
router.register(r'publishers', PublisherViewSet)
