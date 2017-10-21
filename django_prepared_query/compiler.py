from django.db.models.sql.compiler import SQLCompiler
from django.db.models.sql.constants import CURSOR
from .operations import PreparedOperationsFactory


class PrepareSQLCompiler(SQLCompiler):
    def prepare_sql(self):
        if self.query.prepare_statement_sql:
            return self.query.prepare_statement_sql, self.query.prepare_statement_sql_params
        sql, params = self.as_sql()
        arguments = []
        fixed_sql_params = []
        for param in params:
            prepare_param = self.query.prepare_params_by_hash.get(param)
            if not prepare_param:
                fixed_sql_params.append(param)
                continue
            arguments.append(prepare_param.field_type.db_type(self.connection))
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
    def as_sql(self, with_limits=True, with_col_aliases=False):
        self.pre_sql_setup()
        prepare_params_values = self.query.prepare_params_values
        params_order = self.query.prepare_params_order
        arguments = ','.join('%s' for _ in range(len(params_order)))
        params = []
        for param_name in params_order:
            params.append(prepare_params_values[param_name])
        return 'execute %s(%s);' % (self.query.prepare_statement_name, arguments), params
