from collections import Sequence
from django import get_version
from django.db.models import QuerySet, Model
from django.db import connections
from django.db.models.lookups import IsNull, In
from django.core.exceptions import ValidationError
from .query import PrepareQuery, ExecutePreparedQuery
from .params import BindParam
from .utils import get_where_nodes
from .exceptions import PreparedStatementException, QueryNotPrepared, IncorrectBindParameter, \
    OperationOnPreparedStatement, NotSupportedLookup


class PreparedQuerySet(QuerySet):
    def __init__(self, model=None, query=None, using=None, hints=None):
        super(PreparedQuerySet, self).__init__(model=model, query=query, using=using, hints=hints)
        if not query and not isinstance(self.query, ExecutePreparedQuery):
            self.query = PrepareQuery(self.model)
        self.prepared = False
        self.prepare_placeholders = []

    def __repr__(self):
        if self.prepared:
            prepare_query = self.query.prepare_statement_sql % self.query.prepare_statement_sql_params
            arguments = self.query.prepare_params_order
            return 'PreparedQuerySet <%s (%s)>' % (prepare_query, ', '.join(arguments))
        return super(PreparedQuerySet, self).__repr__()

    def __iter__(self):
        self._check_prepared('PreparedQuerySet object is not iterable')
        return self._base_iter()  # pragma: no cover

    def __len__(self):
        self._check_prepared('PreparedQuerySet object has no len()')
        return super(PreparedQuerySet, self).__len__()  # pragma: no cover

    def __bool__(self):
        self._check_prepared('PreparedQuerySet can\'t be fetched without calling execute method')
        return super(PreparedQuerySet, self).__bool__()  # pragma: no cover

    def __getitem__(self, item):
        self._check_prepared('PreparedQuerySet can\'t be fetched without calling execute method')
        return super(PreparedQuerySet, self).__getitem__(item)  # pragma: no cover

    def __and__(self, other):
        self._check_prepared('AND not allowed on prepared statement')
        return super(PreparedQuerySet, self).__and__(other)  # pragma: no cover

    def __or__(self, other):
        self._check_prepared('OR not allowed on prepared statement')
        return super(PreparedQuerySet, self).__or__(other)  # pragma: no cover

    def _base_iter(self):
        return super(PreparedQuerySet, self).__iter__()

    def _check_prepared(self, msg):
        if self.prepared:
            raise OperationOnPreparedStatement(msg)

    def _clone_query(self, klass, query=None):
        query = query or self.query
        if get_version().startswith('2'):
            return query.chain(klass=klass)
        else:
            return query.clone(klass=klass)

    def _execute_prepare(self):
        connection = connections[self.db]
        name = self.query.prepare_statement_name
        prepared_statements = getattr(connection, 'prepared_statements', None)
        if prepared_statements is None:
            prepared_statements = {}
        query = None
        if name not in prepared_statements or prepared_statements[name] != connection.connection:
            query = self._clone_query(klass=PrepareQuery)
            query.get_prepare_compiler(self.db).execute_sql()
            prepared_statements[name] = connection.connection
            setattr(connection, 'prepared_statements', prepared_statements)
        self.query = self._clone_query(klass=ExecutePreparedQuery, query=query)
        return self

    def prepare(self):
        # Set field types for BindParams
        for filter_param, is_inner_query in get_where_nodes(self.query):
            expressions_list = filter_param.rhs
            if not isinstance(expressions_list, Sequence):
                expressions_list = [expressions_list]
            for expression in expressions_list:
                if not isinstance(expression, BindParam):
                    continue
                if type(filter_param) in [IsNull, In]:
                    raise NotSupportedLookup(
                        '%s lookup isn\'t supported in prepared statements' % filter_param.lookup_name)
                if is_inner_query:
                    self.query.add_prepare_param(expression)
                    prepare_param = expression
                else:
                    prepare_param = self.query.prepare_params_by_hash[expression.hash]
                if not prepare_param.field_type:
                    prepare_param.field_type = filter_param.lhs.output_field
        for name, prepare_param in self.query.prepare_params_by_hash.items():
            if not prepare_param.field_type:
                raise PreparedStatementException('Field type is required for %s' % name)
        query = self._clone_query(klass=PrepareQuery)
        query.get_prepare_compiler(self.db).prepare_sql()
        self.query = query
        self.prepared = True
        return self

    def execute(self, **kwargs):
        if not self.prepared:
            raise QueryNotPrepared('Query isn\'t prepared!')
        params = set(kwargs.keys())
        if params != self.query.prepare_params_names:
            raise IncorrectBindParameter('Incorrect params')
        # validate input parameters
        for prepare_param in self.query.prepare_params_by_hash.values():
            field = prepare_param.field_type
            name = prepare_param.name
            param = kwargs.get(name)
            if isinstance(param, Model):
                param = param._get_pk_val()
            try:
                param = field.get_prep_value(param)
            except:
                raise ValidationError('%s is incorrect type for %s parameter' % (param, name))
            field.run_validators(param)
            kwargs[name] = param
        self._execute_prepare()
        self.query.prepare_params_values = kwargs
        qs = self._clone()
        return list(qs._base_iter())

    def iterator(self, *args, **kwargs):
        self._check_prepared('Iterator not allowed on prepared statement')
        return super(PreparedQuerySet, self).iterator(*args, **kwargs)  # pragma: no cover

    def aggregate(self, *args, **kwargs):
        self._check_prepared('Aggregate not allowed on prepared statement')
        return super(PreparedQuerySet, self).aggregate(*args, **kwargs)  # pragma: no cover

    def count(self):
        self._check_prepared('Count not allowed on prepared statement')
        return super(PreparedQuerySet, self).count()  # pragma: no cover

    def get(self, *args, **kwargs):
        self._check_prepared('Get not allowed on prepared statement')
        return super(PreparedQuerySet, self).get(*args, **kwargs)  # pragma: no cover

    def create(self, **kwargs):
        self._check_prepared('Create not allowed on prepared statement')
        return super(PreparedQuerySet, self).create(**kwargs)  # pragma: no cover

    def bulk_create(self, objs, batch_size=None):
        self._check_prepared('Bulk Create not allowed on prepared statement')
        return super(PreparedQuerySet, self).bulk_create(objs, batch_size)  # pragma: no cover

    def get_or_create(self, defaults=None, **kwargs):
        self._check_prepared('Get or create not allowed on prepared statement')
        return super(PreparedQuerySet, self).get_or_create(defaults=defaults, **kwargs)  # pragma: no cover

    def update_or_create(self, defaults=None, **kwargs):
        self._check_prepared('Update or create not allowed on prepared statement')
        return super(PreparedQuerySet, self).update_or_create(defaults=defaults, **kwargs)  # pragma: no cover

    def _earliest_or_latest(self, *args, **kwargs):
        self._check_prepared('Earliest or latest not allowed on prepared statement')
        return super(PreparedQuerySet, self).\
            _earliest_or_latest(*args, **kwargs)  # pragma: no cover

    def first(self):
        self._check_prepared('First not allowed on prepared statement')
        return super(PreparedQuerySet, self).first()  # pragma: no cover

    def last(self):
        self._check_prepared('Last not allowed on prepared statement')
        return super(PreparedQuerySet, self).last()  # pragma: no cover

    def in_bulk(self, *args, **kwargs):
        self._check_prepared('Operation not allowed on prepared statement')
        return super(PreparedQuerySet, self).in_bulk(*args, **kwargs)  # pragma: no cover

    def delete(self):
        self._check_prepared('Delete not allowed on prepared statement')
        return super(PreparedQuerySet, self).delete()  # pragma: no cover

    def update(self, **kwargs):
        self._check_prepared('Update not allowed on prepared statement')
        return super(PreparedQuerySet, self).update(**kwargs)  # pragma: no cover

    def exists(self):
        self._check_prepared('Exists not allowed on prepared statement')
        return super(PreparedQuerySet, self).exists()  # pragma: no cover

    def raw(self, raw_query, params=None, translations=None, using=None):
        self._check_prepared('Raw not allowed on prepared statement')
        return super(PreparedQuerySet, self).raw(raw_query, params=params,
                                                translations=translations, using=using)  # pragma: no cover

    def values(self, *fields, **expressions):
        self._check_prepared('Values not allowed on prepared statement')
        return super(PreparedQuerySet, self).values(*fields, **expressions)  # pragma: no cover

    def values_list(self, *fields, **kwargs):
        self._check_prepared('Values list not allowed on prepared statement')
        return super(PreparedQuerySet, self).values_list(*fields, **kwargs)  # pragma: no cover

    def dates(self, field_name, kind, order='ASC'):
        self._check_prepared('Dates not allowed on prepared statement')
        return super(PreparedQuerySet, self).dates(field_name, kind, order)  # pragma: no cover

    def datetimes(self, field_name, kind, order='ASC', tzinfo=None):
        self._check_prepared('Datetimes not allowed on prepared statement')
        return super(PreparedQuerySet, self).datetimes(field_name, kind, order, tzinfo)  # pragma: no cover

    def none(self):
        self._check_prepared('None not allowed on prepared statement')
        return super(PreparedQuerySet, self).none()  # pragma: no cover

    def all(self):
        self._check_prepared('All not allowed on prepared statement')
        return super(PreparedQuerySet, self).all()  # pragma: no cover

    def _filter_or_exclude(self, negate, *args, **kwargs):
        self._check_prepared('Filter not allowed on prepared statement')
        return super(PreparedQuerySet, self)._filter_or_exclude(negate, *args, **kwargs)  # pragma: no cover

    def select_related(self, *fields):
        self._check_prepared('Select related not allowed on prepared statement')
        return super(PreparedQuerySet, self).select_related(*fields)  # pragma: no cover

    def prefetch_related(self, *lookups):
        self._check_prepared('Prefetch related not allowed on prepared statement')
        return super(PreparedQuerySet, self).prefetch_related(*lookups)  # pragma: no cover

    def annotate(self, *args, **kwargs):
        self._check_prepared('Annotate not allowed on prepared statement')
        return super(PreparedQuerySet, self).annotate(*args, **kwargs)  # pragma: no cover

    def order_by(self, *field_names):
        self._check_prepared('Order by not allowed on prepared statement')
        return super(PreparedQuerySet, self).order_by(*field_names)  # pragma: no cover

    def distinct(self, *field_names):
        self._check_prepared('Distinct not allowed on prepared statement')
        return super(PreparedQuerySet, self).distinct(*field_names)  # pragma: no cover

    def extra(self, select=None, where=None, params=None, tables=None,
              order_by=None, select_params=None):
        self._check_prepared('Extra not allowed on prepared statement')
        return super(PreparedQuerySet, self).extra(select, where, params, tables,
                                                  order_by, select_params)  # pragma: no cover

    def reverse(self):
        self._check_prepared('Reverse not allowed on prepare statement')
        return super(PreparedQuerySet, self).reverse()  # pragma: no cover

    def defer(self, *fields):
        self._check_prepared('Defer not allowed on prepare statement')
        return super(PreparedQuerySet, self).defer(*fields)  # pragma: no cover

    def only(self, *fields):
        self._check_prepared('Only not allowed on prepare statement')
        return super(PreparedQuerySet, self).only(*fields)  # pragma: no cover

    def using(self, alias):
        self._check_prepared('Using not allowed on prepare statement')
        return super(PreparedQuerySet, self).using(alias)  # pragma: no cover
