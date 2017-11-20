from django import get_version
from django.db import connections
from django.db.models.sql.query import Query
from .compiler import PrepareSQLCompiler, ExecutePrepareSQLCompiler
from .exceptions import IncorrectBindParameter


class PrepareQuery(Query):
    def __init__(self, *args, **kwargs):
        super(PrepareQuery, self).__init__(*args, **kwargs)
        self.prepare_params_by_hash = {}
        self.prepare_params_names = set()
        self.prepare_params_order = []
        self.prepare_statement_name = ''
        self.prepare_statement_sql = None
        self.prepare_statement_sql_params = ()

    def _clone_prepared_data(self, query):
        query.prepare_params_by_hash = self.prepare_params_by_hash
        query.prepare_params_names = self.prepare_params_names
        query.prepare_params_order = self.prepare_params_order
        query.prepare_statement_name = self.prepare_statement_name
        query.prepare_statement_sql = self.prepare_statement_sql
        query.prepare_statement_sql_params = self.prepare_statement_sql_params
        return query

    def set_prepare_statement_name(self, name):
        self.prepare_statement_name = name

    def set_prepare_statement_sql(self, sql, params):
        self.prepare_statement_sql = sql
        self.prepare_statement_sql_params = params

    def set_prepare_params_order(self, order):
        self.prepare_params_order = order

    def clone(self, *args, **kwargs):
        if get_version().startswith('2'):
            query = super(PrepareQuery, self).clone()
        else:
            query = super(PrepareQuery, self).clone(*args, **kwargs)
        self._clone_prepared_data(query)
        return query

    def add_prepare_param(self, prepare_param):
        if prepare_param.hash in self.prepare_params_by_hash:
            return
        if prepare_param.name in self.prepare_params_names:
            raise IncorrectBindParameter('\'%s\' parameter used multiple times' % prepare_param.name)
        self.prepare_params_by_hash[prepare_param.hash] = prepare_param
        self.prepare_params_names.add(prepare_param.name)

    def get_prepare_compiler(self, using=None, connection=None):
        if using is None and connection is None:  # pragma: no cover
            raise ValueError("Need either using or connection")
        if using:
            connection = connections[using]
        return PrepareSQLCompiler(self, connection, using)


class ExecutePrepareQuery(PrepareQuery):
    def __init__(self, *args, **kwargs):  # pragma: no cover
        super(PrepareQuery, self).__init__(*args, **kwargs)
        self.prepare_params_values = {}

    def clone(self, klass=None, memo=None, **kwargs):
        query = super(ExecutePrepareQuery, self).clone(klass=klass, memo=memo, **kwargs)
        query.prepare_params_values = self.prepare_params_values
        return query

    def get_compiler(self, using=None, connection=None):
        if using is None and connection is None:  # pragma: no cover
            raise ValueError("Need either using or connection")
        if using:
            connection = connections[using]
        return ExecutePrepareSQLCompiler(self, connection, using)
