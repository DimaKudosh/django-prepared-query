from django.db.models import QuerySet
from django.db import connections, transaction
from .query import PrepareQuery, ExecutePrepareQuery


class PrepareQuerySet(QuerySet):
    def __init__(self, *args, **kwargs):
        super(PrepareQuerySet, self).__init__(*args, **kwargs)
        self.prepared = False

    def prepare(self):
        assert self.query.can_filter(), 'Cannot update a query once a slice has been taken.'
        query = self.query.clone(klass=PrepareQuery)
        with transaction.atomic(using=self.db, savepoint=False):
            rows = query.get_compiler(self.db).execute_sql()
            print(rows)
        self.prepared = True
        self.query = query.clone(klass=ExecutePrepareQuery)
        return self

    def execute(self, **kwargs):
        if not self.prepared:
            return Exception('Prepare statement not created!')
        qs = self._clone()
        return list(qs)

