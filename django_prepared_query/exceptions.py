class PreparedStatementException(Exception):
    pass


class QueryNotPrepared(PreparedStatementException):
    pass


class IncorrectBindParameter(PreparedStatementException):
    pass


class OperationOnPreparedStatement(PreparedStatementException):
    pass


class NotSupportedLookup(PreparedStatementException):
    pass
