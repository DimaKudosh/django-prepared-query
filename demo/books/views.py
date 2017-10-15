from rest_framework import viewsets
from .models import Publisher
from .serializers import PublisherSerializer


Publisher.objects.setup_publisher_by_name()


class PublisherViewSet(viewsets.ModelViewSet):
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer

    def get_queryset(self):
        return Publisher.objects.filter(name='Jay Walker')
