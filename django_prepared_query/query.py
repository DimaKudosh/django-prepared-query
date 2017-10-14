from django.db import connections
from django.db.models.sql.query import Query
from .compiler import PrepareSQLCompiler, ExecutePrepareSQLCompiler


class PrepareQuery(Query):
    def get_compiler(self, using=None, connection=None):
        if using is None and connection is None:
            raise ValueError("Need either using or connection")
        if using:
            connection = connections[using]
        return PrepareSQLCompiler(self, connection, using)


class ExecutePrepareQuery(Query):
    def get_compiler(self, using=None, connection=None):
        if using is None and connection is None:
            raise ValueError("Need either using or connection")
        if using:
            connection = connections[using]
        return ExecutePrepareSQLCompiler(self, connection, using)
