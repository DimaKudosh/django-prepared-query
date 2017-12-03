from django.test import TestCase
from django.db.models import Count
from test_app.models import Author, Book
from django_prepared_query import OperationOnPreparedStatement


class PreparedStatementsTestCase(TestCase):
    def setUp(self):
        self.prepared_qs = Author.objects.prepare()

    def test_prepare_queryset_representation(self):
        representation = repr(self.prepared_qs)
        self.assertTrue(representation.startswith('PreparedQuerySet'))

    def test_iter_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            list(self.prepared_qs)

    def test_len_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            len(self.prepared_qs)

    def test_bool_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            bool(self.prepared_qs)

    def test_getitem_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            item = self.prepared_qs[0]

    def test_and_on_prepared_statement(self):
        another = Author.objects.prepare()
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs & another

    def test_or_on_prepared_statement(self):
        another = Author.objects.prepare()
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs | another

    def test_filter_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs.filter(name='some')

    def test_exclude_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs.exclude(name='some')

    def test_select_related_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs.select_related('book_set')

    def test_prefetch_related_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs.prefetch_related('books_set')

    def test_annotate_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs.annotate(books_count=Count('books_set'))

    def test_order_by_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs.order_by('name')

    def test_distinct_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs.distinct('name')

    def test_extra_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs.extra({'select': '1'})

    def test_reverse_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs.reverse()

    def test_defer_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs.defer('name')

    def test_only_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs.only('name')

    def test_using_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs.using('default')

    def test_iterator_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs.iterator()

    def test_aggregate_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs.aggregate(total=Count('book_set'))

    def test_count_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs.count()

    def test_get_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs.get(id=1)

    def test_create_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs.create(name='some', age=50, gender='m')

    def test_bulk_create_on_prepared_statement(self):
        authors = [Author(name='some', age=50, gender='m')]
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs.bulk_create(authors)

    def test_get_or_create_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs.get_or_create(id=1, defaults={'name': 'some', 'age': 50, 'gender': 'm'})

    def test_update_or_create_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs.update_or_create(id=1, defaults={'name': 'some', 'age': 50, 'gender': 'm'})

    def test_earliest_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs.earliest()

    def test_latest_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs.latest()

    def test_first_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs.first()

    def test_last_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs.last()

    def test_in_bulk_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs.in_bulk()

    def test_delete_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs.delete()

    def test_update_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs.update(age=10)

    def test_exists_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs.exists()

    def test_raw_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs.raw('SELECT 1;')

    def test_values_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs.values('name')

    def test_values_list_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs.values_list('name')

    def test_dates_on_prepared_statement(self):
        prepared_qs = Book.objects.prepare()
        with self.assertRaises(OperationOnPreparedStatement):
            prepared_qs.dates('pubdate', 'year')

    def test_datetimes_on_prepared_statement(self):
        prepared_qs = Book.objects.prepare()
        with self.assertRaises(OperationOnPreparedStatement):
            prepared_qs.datetimes('pubdate', 'year')

    def test_none_on_prepared_statement(self):
        with self.assertRaises(OperationOnPreparedStatement):
            self.prepared_qs.none()
