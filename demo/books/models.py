from django.db import models
from .managers import PublisherManager, PreparePublisherManager


class Author(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()


class Publisher(models.Model):
    objects = PublisherManager()
    prepared_objects = PreparePublisherManager()
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
