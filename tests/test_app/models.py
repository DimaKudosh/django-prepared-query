from django.db import models
from django_prepared_query import PrepareManager


class Author(models.Model):
    GENDER_CHOICES = (
        ('f', 'Female'),
        ('m', 'Male'),
    )
    objects = PrepareManager()
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)


class Publisher(models.Model):
    objects = PrepareManager()
    name = models.CharField(max_length=300)
    num_awards = models.IntegerField()


class Book(models.Model):
    objects = PrepareManager()
    name = models.CharField(max_length=300)
    pages = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    rating = models.FloatField()
    authors = models.ManyToManyField(Author)
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)
    pubdate = models.DateField()
