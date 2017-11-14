from datetime import date
from django.test import TestCase
from django.db.models import Case, When, CharField, BooleanField
from test_app.models import Author, Publisher, Book
from django_prepared_query import BindParam, QueryNotPrepared, IncorrectBindParameter, PreparedStatementException


class PreparedStatementsTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        Author.objects.create(name='Kazuo Ishiguro', age=50, gender='m')
        Author.objects.create(name='Bob Dylan', age=50, gender='m')
        author = Author.objects.create(name='Svetlana Alexievich', age=50, gender='f')
        Author.objects.create(name='Patrick Modiano', age=50, gender='m')
        publisher = Publisher.objects.create(name='Test Publisher', num_awards=43)
        book = Book.objects.create(name='The Unwomanly Face of War', pages=300, price='200.00', rating=4.65,
                            publisher=publisher, pubdate=date.today())
        book.authors.add(author)

    @classmethod
    def tearDownClass(cls):
        Author.objects.delete()
        Book.objects.delete()
        Publisher.objects.delete()

    def test_execute_on_not_prepared_statement(self):
        qs = Author.objects.all()
        with self.assertRaises(QueryNotPrepared):
            qs.execute()

    def test_execute_params(self):
        prepared_qs = Author.objects.filter(name=BindParam('name')).prepare()
        with self.assertRaises(IncorrectBindParameter):
            prepared_qs.execute()
            prepared_qs.execute(wrong_param=1)
            prepared_qs.execute(name='Bob Dylan', another_param=1)

    def test_execute_param_without_type(self):
        qs = Author.objects.annotate(
            is_specified_gender=Case(
                When(gender=BindParam('gender'), then=True),
                default=False,
                output_field=BooleanField())
        )
        with self.assertRaises(PreparedStatementException):
            qs.prepare()

    def test_prepare_statement(self):
        prepared_qs = Author.objects.filter(name=BindParam('name')).prepare()
        empty_qs = Author.objects.filter(name='Not Exist')
        self.assertListEqual(prepared_qs.execute(name='Not Exist'), list(empty_qs))
        name = 'Svetlana Alexievich'
        qs = Author.objects.filter(name=name)
        self.assertListEqual(prepared_qs.execute(name=name), list(qs))

    def test_prepare_statement_with_field_type(self):
        prepared_qs = Author.objects.annotate(
            is_specified_gender=Case(
                When(gender=BindParam('gender', CharField()), then=True),
                default=False,
                output_field=BooleanField())
        ).order_by('gender').values_list('is_specified_gender', flat=True).prepare()
        is_female = prepared_qs.execute(gender='f')
        self.assertListEqual(is_female, [True, False, False, False])

    def test_prepare_without_params(self):
        prepared_qs = Author.objects.order_by('name').prepare()
        expected_result = list(Author.objects.order_by('name').all())
        self.assertListEqual(prepared_qs.execute(), expected_result)

    def test_prepare_values_list(self):
        prepared_qs = Author.objects.values_list('name', flat=True).order_by('name').prepare()
        expected_result = list(Author.objects.values_list('name', flat=True).order_by('name'))
        self.assertListEqual(prepared_qs.execute(), expected_result)

    def test_prepare_values(self):
        prepared_qs = Author.objects.values('name').order_by('name').prepare()
        expected_result = list(Author.objects.values('name').order_by('name'))
        self.assertListEqual(prepared_qs.execute(), expected_result)

    def test_select_related(self):
        prepared_qs = Book.objects.select_related('publisher').prepare()
        with self.assertNumQueries(2):  # Prepare and execute
            book = prepared_qs.execute()[0]
            publisher = book.publisher

    def test_prefetch_related(self):
        author_name = 'Svetlana Alexievich'
        prepared_qs = Author.objects.filter(name=author_name).prefetch_related('books').prepare()
        with self.assertNumQueries(3):  # Prepare, execute and prefetch query
            author = prepared_qs.execute()[0]
        self.assertEqual(author.books.count(), 1)

    def test_only(self):
        author_name = 'Svetlana Alexievich'
        prepared_qs = Author.objects.filter(name=author_name).only('id').prepare()
        with self.assertNumQueries(2):  # Prepare, execute
            author = prepared_qs.execute()[0]
        with self.assertNumQueries(1):
            author_id = author.id
            author_name = author.name  # Deferred field must generate query

    def test_defer(self):
        author_name = 'Svetlana Alexievich'
        prepared_qs = Author.objects.filter(name=author_name).defer('name').prepare()
        with self.assertNumQueries(2):  # Prepare, execute
            author = prepared_qs.execute()[0]
        with self.assertNumQueries(1):
            author_id = author.id
            author_name = author.name  # Deferred field must generate query

    def test_same_prepare(self):
        with self.assertNumQueries(2):
            Author.objects.all().prepare().execute()
        with self.assertNumQueries(1):
            Author.objects.all().prepare().execute()

    def test_same_bind_param(self):
        with self.assertRaises(IncorrectBindParameter):
            Author.objects.filter(id=BindParam('param'), name=BindParam('param'))
