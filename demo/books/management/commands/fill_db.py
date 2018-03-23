from datetime import datetime
from mixer.backend.django import mixer
from django.core.management.base import BaseCommand, CommandError
from books.models import Book, Author, Publisher


class Command(BaseCommand):
    def handle(self, *args, **options):
        publishers = mixer.cycle(15).blend(Publisher)
        authors = mixer.cycle(50).blend(Author, age=(i for i in range(20, 70)))
        books = mixer.cycle(1000).blend(Book, pubdate=datetime.now(), authors=mixer.RANDOM, publisher=mixer.SELECT)
