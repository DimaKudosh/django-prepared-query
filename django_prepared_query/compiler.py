from django.db.models.sql.compiler import SQLCompiler
from django.db.models.sql.constants import CURSOR, MULTI
from django.db.models import AutoField, BigAutoField, IntegerField, BigIntegerField
from .operations import PreparedOperationsFactory


class PrepareSQLCompiler(SQLCompiler):
    def prepare_sql(self):
        if self.query.prepare_statement_sql:
            return self.query.prepare_statement_sql, self.query.prepare_statement_sql_params
        sql, params = self.as_sql()
        arguments = []
        fixed_sql_params = []
        for param in params:
            for prepare_param in self.query.prepare_params_by_name.values():
                if isinstance(param, str) and prepare_param.hash in param:
                    field = prepare_param.field_type
                    if isinstance(field, BigAutoField):
                        field = BigIntegerField()
                    elif isinstance(field, AutoField):
                        field = IntegerField()
                    arguments.append(field.db_type(self.connection))
                    break
            else:
                fixed_sql_params.append(param)
        prepared_operations = PreparedOperationsFactory.create(self.connection.vendor)
        prepare_statement = prepared_operations.prepare_sql(name=self.query.prepare_statement_name,
                                                            arguments=arguments, sql=sql)
        placeholders = tuple(prepared_operations.prepare_placeholder(i) for i in range(1, len(arguments) + 1))
        sql_with_placeholders = prepare_statement.format(*placeholders)
        self.query.set_prepare_statement_sql(sql_with_placeholders, fixed_sql_params)
        return sql_with_placeholders, fixed_sql_params

    def execute_sql(self, result_type=CURSOR, chunked_fetch=False):
        with self.connection.cursor() as cursor:
            sql, params = self.prepare_sql()
            cursor.execute(sql, params)
            return cursor


class ExecutePrepareSQLCompiler(SQLCompiler):
    def __init__(self, query, connection, using):
        super(ExecutePrepareSQLCompiler, self).__init__(query, connection, using)
        self.params_order = self.query.prepare_params_order
        prepare_params_values = self.query.prepare_params_values
        params = []
        for param_name in self.params_order:
            params.append(prepare_params_values[param_name])
        self.params = params
        self.prepared_operations = PreparedOperationsFactory.create(self.connection.vendor)

    def as_sql(self, with_limits=True, with_col_aliases=False):
        self.pre_sql_setup()
        execute_statement = self.prepared_operations.execute_sql(name=self.query.prepare_statement_name,
                                                                 arguments=self.params_order)
        params = self.params if self.params and not self.prepared_operations.has_setup() else ()
        return execute_statement, params

    def setup_execute_sql(self):
        if not self.prepared_operations.has_setup():
            return
        setup_sql = self.prepared_operations.setup_execute_sql(self.params_order)
        if not setup_sql:
            return
        cursor = self.connection.cursor()
        try:
            cursor.execute(setup_sql, self.params)
        except Exception as original_exception:
            try:
                cursor.close()
            except Exception:
                pass
            raise original_exception

    def execute_sql(self, result_type=MULTI, chunked_fetch=False):
        self.setup_execute_sql()
        return super(ExecutePrepareSQLCompiler, self).execute_sql(result_type, chunked_fetch)
