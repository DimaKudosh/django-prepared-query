from rest_framework import routers
from .views import PublisherViewSet, PreparedPublisherViewSet, BookViewSet, PreparedBookViewSet


router = routers.DefaultRouter()
router.register(r'publishers', PublisherViewSet)
router.register(r'books', BookViewSet)
urlpatterns = router.urls

prepared_router = routers.DefaultRouter()
prepared_router.register(r'publishers', PreparedPublisherViewSet)
prepared_router.register(r'books', PreparedBookViewSet)
prepared_urlpatterns = prepared_router.urls
