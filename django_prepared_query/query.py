from django.db import connections
from django.db.models.sql.query import Query
from .compiler import PrepareSQLCompiler, ExecutePrepareSQLCompiler


class PrepareQuery(Query):
    def __init__(self, *args, **kwargs):
        super(PrepareQuery, self).__init__(*args, **kwargs)
        self.prepare_params_by_name = {}
        self.prepare_params_by_hash = {}
        self.prepare_params_order = []
        self.prepare_statement_name = ''
        self.prepare_statement_sql = None
        self.prepare_statement_sql_params = ()

    def set_prepare_statement_name(self, name):
        self.prepare_statement_name = name

    def set_prepare_statement_sql(self, sql, params):
        self.prepare_statement_sql = sql
        self.prepare_statement_sql_params = params

    def clone(self, klass=None, memo=None, **kwargs):
        query = super(PrepareQuery, self).clone(klass=klass, memo=memo, **kwargs)
        query.prepare_params_by_name = self.prepare_params_by_name
        query.prepare_params_by_hash = self.prepare_params_by_hash
        query.prepare_params_order = self.prepare_params_order
        query.prepare_statement_name = self.prepare_statement_name
        query.prepare_statement_sql = self.prepare_statement_sql
        query.prepare_statement_sql_params = self.prepare_statement_sql_params
        return query

    def add_prepare_param(self, prepare_param):
        self.prepare_params_by_name[prepare_param.name] = prepare_param
        self.prepare_params_by_hash[prepare_param.hash] = prepare_param
        self.prepare_params_order.append(prepare_param.name)

    def get_prepare_compiler(self, using=None, connection=None):
        if using is None and connection is None:
            raise ValueError("Need either using or connection")
        if using:
            connection = connections[using]
        return PrepareSQLCompiler(self, connection, using)


class ExecutePrepareQuery(PrepareQuery):
    def __init__(self, *args, **kwargs):
        super(PrepareQuery, self).__init__(*args, **kwargs)
        self.prepare_params_values = {}

    def clone(self, klass=None, memo=None, **kwargs):
        query = super(ExecutePrepareQuery, self).clone(klass=klass, memo=memo, **kwargs)
        query.prepare_params_values = self.prepare_params_values
        return query

    def get_compiler(self, using=None, connection=None):
        if using is None and connection is None:
            raise ValueError("Need either using or connection")
        if using:
            connection = connections[using]
        return ExecutePrepareSQLCompiler(self, connection, using)
