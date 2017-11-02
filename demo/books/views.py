from rest_framework import viewsets
from rest_framework.response import Response
from .models import Publisher
from .serializers import PublisherSerializer


class PublisherViewSet(viewsets.ModelViewSet):
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer

    def retrieve(self, request, *args, **kwargs):
        publisher = Publisher.objects.get_by_id(kwargs['pk'])
        serializer = PublisherSerializer(publisher)
        return Response(serializer.data)


class PreparedPublisherViewSet(viewsets.ModelViewSet):
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer

    def retrieve(self, request, *args, **kwargs):
        publisher = Publisher.prepared_objects.get_by_id(kwargs['pk'])
        serializer = PublisherSerializer(publisher)
        return Response(serializer.data)
