from django.test import TestCase
from django.db.models import Case, When, CharField, BooleanField
from test_app.models import Author
from django_prepared_query import BindParam, QueryNotPrepared, IncorrectBindParameter, PreparedStatementException


class PreparedStatementsTestCase(TestCase):
    def setUp(self):
        Author.objects.create(name='Kazuo Ishiguro', age=50, gender='m')
        Author.objects.create(name='Bob Dylan', age=50, gender='m')
        Author.objects.create(name='Svetlana Alexievich', age=50, gender='f')
        Author.objects.create(name='Patrick Modiano', age=50, gender='m')

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

    def test_prepare_queryset_representation(self):
        prepared_qs = Author.objects.prepare()
        representation = repr(prepared_qs)
        self.assertTrue(representation.startswith('PrepareQuerySet'))
