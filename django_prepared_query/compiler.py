from django.db.models.sql.compiler import SQLCompiler
from django.db.models.sql.constants import CURSOR


class PrepareSQLCompiler(SQLCompiler):
    prepare_statement_name = 'fooplan'

    def prepare_sql(self):
        sql, params = self.as_sql()
        arguments = []
        for param in params:
            prepare_param = self.query.prepare_params_by_hash.get(param)
            if not prepare_param:
                continue
            arguments.append(prepare_param.field_type.db_type(self.connection))
        prepare_statement = 'PREPARE %s (%s) AS' % (self.prepare_statement_name, ','.join(arguments))
        sql = '%s %s;' % (prepare_statement, sql)
        placeholders = tuple(i for i in range(1, len(params) + 1))
        sql_with_placeholders = sql.format(*placeholders)
        print(sql_with_placeholders)
        return sql_with_placeholders, ()

    def execute_sql(self, result_type=CURSOR, chunked_fetch=False):
        with self.connection.cursor() as cursor:
            sql, params = self.prepare_sql()
            cursor.execute(sql, params)
            return cursor


class ExecutePrepareSQLCompiler(SQLCompiler):
    def as_sql(self, with_limits=True, with_col_aliases=False):
        self.pre_sql_setup()
        prepare_params_values = self.query.prepare_params_values
        arguments = ','.join('%s' for _ in range(len(prepare_params_values)))
        return 'execute fooplan(%s);' % arguments, list(prepare_params_values.values())
