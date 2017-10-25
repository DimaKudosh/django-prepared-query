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
    created_at = models.DateTimeField(auto_now_add=True)


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


class BigAutoModel(models.Model):
    objects = PrepareManager()
    id = models.BigAutoField(primary_key=True)


class AllFieldsModel(models.Model):
    objects = PrepareManager()
    big_int = models.BigIntegerField()
    binary = models.BinaryField()
    boolean = models.BooleanField()
    char = models.CharField(max_length=8)
    date = models.DateField()
    datetime = models.DateTimeField()
    decimal = models.DecimalField(max_digits=5, decimal_places=2)
    duration = models.DurationField()
    email = models.EmailField()
    file = models.FileField()
    file_path = models.FilePathField()
    float = models.FloatField()
    image = models.ImageField()
    int = models.IntegerField()
    generic_ip_address = models.GenericIPAddressField()
    null_boolean = models.NullBooleanField()
    positive_int = models.PositiveIntegerField()
    positive_small_int = models.PositiveSmallIntegerField()
    slug = models.SlugField()
    small_int = models.SmallIntegerField()
    text = models.TextField()
    time = models.TimeField()
    url = models.URLField()
    uuid = models.UUIDField()
    foreign_key = models.ForeignKey(BigAutoModel)
