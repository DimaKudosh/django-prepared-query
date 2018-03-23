from django.test import TransactionTestCase
from django.db import connections
from test_app.models import Book
from django_prepared_query.statements_pool import statements_pool


class StatementsPoolTestCase(TransactionTestCase):
    def test_query_after_connection_close(self):
        prepared_qs = Book.objects.prepare()
        with self.assertNumQueries(2):  # Prepare and execute
            prepared_qs.execute()
        with self.assertNumQueries(1):  # Execute
            prepared_qs.execute()
        connections.close_all()
        with self.assertNumQueries(2):  # Prepare and execute
            prepared_qs.execute()

    def test_statements_pool_clear(self):
        prepared_qs = Book.objects.prepare()
        prepared_qs.execute()
        self.assertEqual(len(statements_pool), 1)
        connections.close_all()
        self.assertEqual(len(statements_pool), 0)
