from django.db.models import QuerySet
from django.db import connections
from .query import PrepareQuery, ExecutePrepareQuery
from .params import BindParam
from .utils import generate_random_string, get_where_nodes
from .exceptions import PreparedStatementException, QueryNotPrepared, IncorrectBindParameter


class PrepareQuerySet(QuerySet):
    HASH_LENGTH = 20

    def __init__(self, model=None, query=None, using=None, hints=None):
        super(PrepareQuerySet, self).__init__(model=model, query=query, using=using, hints=hints)
        if not query and not isinstance(self.query, ExecutePrepareQuery):
            self.query = PrepareQuery(self.model)
        self.prepared = False
        self.prepare_placeholders = []

    def _generate_prepare_statement_name(self):
        return '%s_%s' % (self.model._meta.model_name, generate_random_string(self.HASH_LENGTH))

    def _execute_prepare(self):
        connection = connections[self.db]
        query = self.query
        name = query.prepare_statement_name
        prepared_statements = getattr(connection, 'prepared_statements', None)
        if prepared_statements is None:
            prepared_statements = {}
        if name not in prepared_statements or prepared_statements[name] != connection.connection:
            query = query.clone(klass=PrepareQuery)
            query.get_prepare_compiler(self.db).execute_sql()
            prepared_statements[name] = connection.connection
        setattr(connection, 'prepared_statements', prepared_statements)
        self.query = query.clone(klass=ExecutePrepareQuery)
        return self

    def prepare(self):
        assert self.query.can_filter(), 'Cannot prepare a query once a slice has been taken.'
        for filter_param in get_where_nodes(self.query):
            expression = filter_param.rhs
            if not isinstance(expression, BindParam):
                continue
            prepare_param = self.query.prepare_params_by_name[expression.name]
            if not prepare_param.field_type:
                prepare_param.field_type = filter_param.lhs.output_field
        for name, prepare_param in self.query.prepare_params_by_name.items():
            if not prepare_param.field_type:
                raise PreparedStatementException('Field type is required for %s' % name)
        query = self.query.clone(klass=PrepareQuery)
        query.set_prepare_statement_name(self._generate_prepare_statement_name())
        query.get_prepare_compiler(self.db).prepare_sql()
        self.query = query
        self.prepared = True
        return self

    def execute(self, **kwargs):
        if not self.prepared:
            raise QueryNotPrepared('Prepare statement not created!')
        params = set(kwargs.keys())
        prepare_params = set(self.query.prepare_params_order)
        if params != prepare_params:
            raise IncorrectBindParameter('Incorrect params')
        self._execute_prepare()
        self.query.prepare_params_values = kwargs
        qs = self._clone()
        return list(qs)

