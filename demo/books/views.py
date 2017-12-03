from rest_framework import viewsets
from rest_framework.response import Response
from django_prepared_query import BindParam
from .models import Publisher, Book
from .serializers import PublisherSerializer, BookSerializer


class PublisherViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer

    def retrieve(self, request, *args, **kwargs):
        publisher = self.get_queryset().get(pk=kwargs['pk'])
        serializer = PublisherSerializer(publisher)
        return Response(serializer.data)


class PreparedPublisherViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Publisher.prepared_objects.filter(pk=BindParam('pk')).prepare()
    serializer_class = PublisherSerializer

    def retrieve(self, request, *args, **kwargs):
        publisher = self.get_queryset().execute(pk=kwargs['pk'])[0]
        serializer = PublisherSerializer(publisher)
        return Response(serializer.data)


class BookViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Book.objects.select_related('publisher')
    serializer_class = BookSerializer

    def list(self, request, *args, **kwargs):
        author_age = request.GET.get('author_age', 25)
        min_pages = request.GET.get('min_pages', 100)
        max_pages = request.GET.get('max_pages', 1000)
        books = self.get_queryset().filter(authors__age=author_age).filter(pages__gte=min_pages, pages__lte=max_pages)
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)


class PreparedBookViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Book.prepared_objects.select_related('publisher').filter(authors__age=BindParam('author_age')).\
        filter(pages__gte=BindParam('min_pages'), pages__lte=BindParam('max_pages')).prepare()
    serializer_class = BookSerializer

    def list(self, request, *args, **kwargs):
        author_age = request.GET.get('author_age', 25)
        min_pages = request.GET.get('min_pages', 100)
        max_pages = request.GET.get('max_pages', 1000)
        books = self.get_queryset().execute(author_age=author_age, min_pages=min_pages, max_pages=max_pages)
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)
