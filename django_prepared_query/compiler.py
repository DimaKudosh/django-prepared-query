from django.db.models.sql.compiler import SQLCompiler
from django.db.models.sql.constants import CURSOR


class PrepareSQLCompiler(SQLCompiler):
    prepare_statement_name = 'fooplan'

    def prepare_sql(self):
        sql, params = self.as_sql()
        prepare_statement = 'PREPARE %s AS' % self.prepare_statement_name
        sql = '%s %s;' % (prepare_statement, sql)
        return sql, params

    def execute_sql(self, result_type=CURSOR, chunked_fetch=False):
        with self.connection.cursor() as cursor:
            sql, params = self.prepare_sql()
            cursor.execute(sql, params)
            return cursor


class ExecutePrepareSQLCompiler(SQLCompiler):
    def as_sql(self, with_limits=True, with_col_aliases=False):
        self.pre_sql_setup()
        return 'execute fooplan;', ()
