from django.db.models import QuerySet
from django.db import connections, transaction
from .query import PrepareQuery, ExecutePrepareQuery
from .params import BindParam
from .utils import generate_random_string


class PrepareQuerySet(QuerySet):
    HASH_LENGTH = 20

    def __init__(self, *args, **kwargs):
        super(PrepareQuerySet, self).__init__(*args, **kwargs)
        if not isinstance(self.query, ExecutePrepareQuery):
            self.query = PrepareQuery(self.model)
        self.prepared = False
        self.prepare_placeholders = []

    def _generate_prepare_statement_name(self):
        return '%s_%s' % (self.model._meta.model_name, generate_random_string(self.HASH_LENGTH))

    def prepare(self, name=None):
        assert self.query.can_filter(), 'Cannot update a query once a slice has been taken.'
        query = self.query.clone(klass=PrepareQuery)
        for filter_param in query.where.children:
            expression = filter_param.rhs
            if not isinstance(expression, BindParam):
                continue
            prepare_param = query.prepare_params_by_name[expression.name]
            if not prepare_param.field_type:
                prepare_param.field_type = filter_param.lhs.output_field
        for name, prepare_param in query.prepare_params_by_name.items():
            if not prepare_param.field_type:
                raise Exception('Field type is required for %s' % name)
        query.set_prepare_statement_name(self._generate_prepare_statement_name())
        with transaction.atomic(using=self.db, savepoint=False):
            query.get_prepare_compiler(self.db).execute_sql()
        self.prepared = True
        self.query = query.clone(klass=ExecutePrepareQuery)
        return self

    def execute(self, **kwargs):
        if not self.prepared:
            raise Exception('Prepare statement not created!')
        params = set(kwargs.keys())
        prepare_params = set(self.query.prepare_params_by_name.keys())
        if params != prepare_params:
            raise Exception('Incorrect params')
        self.query.prepare_params_values = kwargs
        qs = self._clone()
        return list(qs)

