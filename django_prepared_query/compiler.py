from hashlib import md5
from django.db.models.sql.compiler import SQLCompiler
from django.db.models import AutoField, BigAutoField, IntegerField, BigIntegerField
from .operations import PreparedOperationsFactory


class PrepareSQLCompiler(SQLCompiler):
    def _generate_statement_name(self, sql):
        sql_hash = md5(sql.encode()).hexdigest()
        model_name = self.query.model._meta.model_name
        name = '%s_%s' % (model_name, sql_hash)
        self.query.prepare_statement_name = name
        return name

    def prepare_sql(self):
        if self.query.prepare_statement_sql:
            return self.query.prepare_statement_sql, self.query.prepare_statement_sql_params
        sql, params = self.as_sql()
        name = self._generate_statement_name(sql)
        arguments = []
        fixed_sql_params = []
        prepare_params_ordered = []
        for param in params:
            for prepare_param_hash, prepare_param in self.query.prepare_params_by_hash.items():
                if not isinstance(param, str) or prepare_param_hash not in param:
                    continue
                field = prepare_param.field_type
                if isinstance(field, BigAutoField):
                    field = BigIntegerField()
                elif isinstance(field, AutoField):
                    field = IntegerField()
                arguments.append(field.db_type(self.connection))
                prepare_params_ordered.append(prepare_param_hash)
                break
            else:
                fixed_sql_params.append(param)
        prepared_operations = PreparedOperationsFactory.create(self.connection.vendor)
        prepare_statement = prepared_operations.prepare_sql(name=name,
                                                            arguments=arguments, sql=sql)
        placeholders = tuple(prepared_operations.prepare_placeholder(i) for i in range(1, len(arguments) + 1))
        sql_with_placeholders = prepare_statement.format(*placeholders)
        self.query.set_prepare_statement_sql(sql_with_placeholders, fixed_sql_params)
        self.query.set_prepare_params_order(prepare_params_ordered)
        return sql_with_placeholders, fixed_sql_params

    def execute_sql(self, *args, **kwargs):
        with self.connection.cursor() as cursor:
            sql, params = self.prepare_sql()
            cursor.execute(sql, params)
            return cursor


class ExecutePreparedSQLCompiler(SQLCompiler):
    def __init__(self, query, connection, using):
        super(ExecutePreparedSQLCompiler, self).__init__(query, connection, using)
        self.prepared_operations = PreparedOperationsFactory.create(self.connection.vendor)

    def get_query_params(self):
        prepare_params_values = self.query.prepare_params_values
        params = []
        for param_hash in self.query.prepare_params_order:
            name = self.query.prepare_params_by_hash[param_hash].name
            params.append(prepare_params_values[name])
        return params

    def as_sql(self, with_limits=True, with_col_aliases=False):
        params = self.get_query_params()
        execute_statement = self.prepared_operations.execute_sql(name=self.query.prepare_statement_name,
                                                                 arguments=params)
        params = params if params and not self.prepared_operations.has_setup() else ()
        return execute_statement, params

    def setup_execute_sql(self):
        params = self.get_query_params()
        setup_sql = self.prepared_operations.setup_execute_sql(params)
        if not setup_sql:
            return
        cursor = self.connection.cursor()
        try:
            cursor.execute(setup_sql, params)
        except Exception as original_exception:
            try:
                cursor.close()
            except Exception:
                pass
            raise original_exception

    def execute_sql(self, *args, **kwargs):
        if self.prepared_operations.has_setup():
            self.setup_execute_sql()
        return super(ExecutePreparedSQLCompiler, self).execute_sql(*args, **kwargs)
