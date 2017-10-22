from django.core.exceptions import ImproperlyConfigured


class PreparedOperations:
    def prepare_sql(self, name, arguments, sql):
        raise NotImplementedError

    def execute_sql(self, name, arguments):
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

    def prepare_placeholder(self, index):
        return '$%d' % index


class MySqlPreparedOperations(PreparedOperations):
    pass


class OraclePreparedOperations(PreparedOperations):
    pass


class SqLitePreparedOperations(PreparedOperations):
    pass


class PreparedOperationsFactory:
    MAPPING = {
        'postgresql': PostgresqlPreparedOperations,
        'mysql': MySqlPreparedOperations,
        'sqlite': SqLitePreparedOperations,
        'oracle': OraclePreparedOperations,
    }

    @classmethod
    def create(cls, vendor):
        operations_class = cls.MAPPING.get(vendor)
        if not vendor:
            raise ImproperlyConfigured('Incorrect vendor name for prepared operations')
        return operations_class()
