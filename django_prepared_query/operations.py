from django.core.exceptions import ImproperlyConfigured


class PreparedOperations:
    def prepare_sql(self, name, arguments, sql):
        raise NotImplementedError

    def execute_sql(self, name, arguments):
        raise NotImplementedError

    def setup_execute_sql(self, arguments):
        raise NotImplementedError

    @staticmethod
    def has_setup():
        raise NotImplementedError

    def prepare_placeholder(self, index):
        raise NotImplementedError


class PostgresqlPreparedOperations(PreparedOperations):
    def prepare_sql(self, name, arguments, sql):
        arguments_sql = ''
        if arguments:
            arguments_sql = '(%s)' % ','.join(arguments)
        return 'PREPARE %s %s AS %s;' % (name, arguments_sql, sql)

    def execute_sql(self, name, arguments):
        arguments_sql = ''
        if arguments:
            arguments_sql = '(%s)' % ','.join('%s' for _ in range(len(arguments)))
        return 'EXECUTE %s%s;' % (name, arguments_sql)

    @staticmethod
    def has_setup():
        return False

    def setup_execute_sql(self, arguments):
        return None

    def prepare_placeholder(self, index):
        return '$%d' % index


class MySqlPreparedOperations(PreparedOperations):
    VARIABLE_TEMPLATE = '@var%d'

    def prepare_sql(self, name, arguments, sql):
        return "PREPARE %s FROM \"%s\";" % (name, sql.replace('\\', '\\\\'))

    def execute_sql(self, name, arguments):
        execute_sql = 'EXECUTE %s' % name
        if arguments:
            variables = [self.VARIABLE_TEMPLATE % i for i in range(len(arguments))]
            arguments_sql = ','.join(name for name in variables)
            execute_sql = '%s USING %s' % (execute_sql, arguments_sql)
        return execute_sql + ';'

    @staticmethod
    def has_setup():
        return True

    def setup_execute_sql(self, arguments):
        if not arguments:
            return None
        variables = [self.VARIABLE_TEMPLATE % i for i in range(len(arguments))]
        sql = 'SET %s;' % ','.join(['{} = %s'.format(name) for name in variables])
        return sql

    def prepare_placeholder(self, index):
        return '?'


class OraclePreparedOperations(PreparedOperations):
    pass


class SqLitePreparedOperations(PreparedOperations):
    pass


class PreparedOperationsFactory:
    MAPPING = {
        'postgresql': PostgresqlPreparedOperations(),
        'mysql': MySqlPreparedOperations(),
        'sqlite': SqLitePreparedOperations(),
        'oracle': OraclePreparedOperations(),
    }

    @classmethod
    def create(cls, vendor):
        operations_class = cls.MAPPING.get(vendor)
        if operations_class:
            return operations_class
        raise ImproperlyConfigured('Incorrect vendor name for prepared operations')
