class PreparedStatementException(Exception):
    pass


class QueryNotPrepared(PreparedStatementException):
    pass


class IncorrectBindParameter(PreparedStatementException):
    pass
