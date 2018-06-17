from datetime import date
from django.test import TestCase
from django.db.models import Case, When, CharField, BooleanField, Value, IntegerField, Count
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
        with self.assertRaises(IncorrectBindParameter):
            prepared_qs.execute(wrong_param=1)
        with self.assertRaises(IncorrectBindParameter):
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
        author_names = ['Svetlana Alexievich', 'Kazuo Ishiguro']
        prepared_qs = Author.objects.filter(name__in=author_names).prefetch_related('books').prepare()
        with self.assertNumQueries(3):  # Prepare, execute and prefetch query
            authors = prepared_qs.execute()
            list(authors[0].books.all())
            list(authors[1].books.all())

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

    def test_having_with_repeated_params(self):
        extra_books = 5
        min_books = 6
        prepared_qs = Publisher.objects.annotate(books=Count('book') + BindParam('extra_books', field_type=IntegerField())).\
            filter(books__gte=BindParam('min_books')).prepare()
        qs = Publisher.objects.annotate(books=Count('book') + Value(extra_books, output_field=IntegerField())). \
            filter(books__gte=min_books)
        self.assertListEqual(prepared_qs.execute(extra_books=extra_books, min_books=min_books), list(qs))

    def test_subquery(self):
        name_starts = 'Svetlana'
        prepare_inner_qs = Publisher.objects.filter(name__startswith=BindParam('name'))
        prepare_qs = Book.objects.filter(publisher__in=prepare_inner_qs).prepare()
        inner_qs = Publisher.objects.filter(name__startswith=name_starts)
        qs = Book.objects.filter(publisher__in=inner_qs)
        self.assertListEqual(prepare_qs.execute(name=name_starts), list(qs))

    def test_execute_iterator(self):
        prepared_qs = Author.objects.filter(name=BindParam('name')).prepare()
        authors_iterator = prepared_qs.execute_iterator(name='Bob Dylan')
        author = next(authors_iterator)
        with self.assertRaises(StopIteration):
            next(authors_iterator)

    def test_limit_offset(self):
        prepared_qs = Author.objects.all()[BindParam('start'):BindParam('end')].prepare()
        qs = Author.objects.all()[0:5]
        self.assertListEqual(prepared_qs.execute(start=0, end=5), list(qs))
        prepared_qs = Author.objects.all()[1:BindParam('end')].prepare()
        qs = Author.objects.all()[1:2]
        self.assertListEqual(prepared_qs.execute(end=2), list(qs))
        prepared_qs = Author.objects.all()[BindParam('start'):2].prepare()
        self.assertListEqual(prepared_qs.execute(start=1), list(qs))
        qs = Author.objects.all()[:2]
        prepared_qs = Author.objects.all()[:BindParam('end')].prepare()
        self.assertListEqual(prepared_qs.execute(end=2), list(qs))
        qs = Author.objects.all()[2:]
        prepared_qs = Author.objects.all()[BindParam('start'):].prepare()
        self.assertListEqual(prepared_qs.execute(start=2), list(qs))
        with self.assertRaises(PreparedStatementException):
            Author.objects.all()[::BindParam('step')].prepare()
