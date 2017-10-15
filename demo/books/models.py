from django.db import models
from django_prepared_query import PrepareManager, BindParam


class Author(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()


class PublisherManager(PrepareManager):
    def __init__(self):
        super(PublisherManager, self).__init__()

    def setup_publisher_by_name(self):
        self.prepared_get = self.get_queryset().filter(name=BindParam('name')).prepare()

    def get_publishers_by_name(self, name):
        return self.prepared_get.execute(name=name)


class Publisher(models.Model):
    objects = PublisherManager()
    name = models.CharField(max_length=300)
    num_awards = models.IntegerField()


class Book(models.Model):
    name = models.CharField(max_length=300)
    pages = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    rating = models.FloatField()
    authors = models.ManyToManyField(Author)
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)
    pubdate = models.DateField()
