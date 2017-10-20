from django.core.exceptions import ImproperlyConfigured


class PreparedOperations:
    def prepare_sql(self, name, arguments, sql):
        raise NotImplementedError

    def prepare_placeholder(self, index):
        raise NotImplementedError


class PostgresqlPreparedOperations(PreparedOperations):
    def prepare_sql(self, name, arguments, sql):
        return 'PREPARE %s (%s) AS %s;' % (name, ','.join(arguments), sql)

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
