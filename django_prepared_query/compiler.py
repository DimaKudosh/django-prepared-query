from hashlib import md5
from django.db.models.sql.compiler import SQLCompiler
from django.db.models import AutoField, BigAutoField, IntegerField, BigIntegerField
from .operations import PreparedOperationsFactory
from .params import BindParam


class PrepareSQLCompiler(SQLCompiler):
    def _generate_statement_name(self, sql):
        sql_hash = md5(sql.encode()).hexdigest()
        model_name = self.query.model._meta.model_name
        name = '%s_%s' % (model_name, sql_hash)
        self.query.prepare_statement_name = name
        return name

    def as_sql(self, with_limits=True, with_col_aliases=False):
        """
        Because Django expects that low_mark and high_mark are numbers and it can be BindParam
        instead of number we temporary change limit BindParams to number, compile to sql using
        standard Django as_sql method and then change it back to BindParams.
        """
        query = self.query
        high_mark, low_mark = query.high_mark, query.low_mark
        is_high_mark_bind_param = isinstance(high_mark, BindParam)
        is_low_mark_bind_param = isinstance(low_mark, BindParam)
        if is_high_mark_bind_param:
            query.high_mark = 2 if low_mark else 1
        if is_low_mark_bind_param:
            query.low_mark = 1
        result_sql, params = super(PrepareSQLCompiler, self).as_sql(with_limits, with_col_aliases)
        params = list(params)
        if is_high_mark_bind_param:
            result_sql = result_sql.replace('LIMIT 1', 'LIMIT {}')
            params.append(high_mark.hash)
        if is_low_mark_bind_param:
            result_sql = result_sql.replace('OFFSET 1', 'OFFSET {}')
            params.append(low_mark.hash)
        query.high_mark, query.low_mark = high_mark, low_mark
        return result_sql, tuple(params)

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
                db_type = field.db_type(self.connection)
                for _ in range(prepare_param.size):
                    arguments.append(db_type)
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
            prepare_param = self.query.prepare_params_by_hash[param_hash]
            values = prepare_params_values[prepare_param.name]
            if prepare_param.size > 1:
                params.extend(values)
            else:
                params.append(values)
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
