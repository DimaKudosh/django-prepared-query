from collections import Sequence
from functools import wraps
from django import get_version
from django.db.models import QuerySet, BigIntegerField
from django.db import connections
from django.db.models.lookups import IsNull, In
from django.core.exceptions import ValidationError
from .query import PrepareQuery, ExecutePreparedQuery
from .params import BindParam, BindArray
from .utils import get_where_nodes
from .exceptions import PreparedStatementException, QueryNotPrepared, IncorrectBindParameter, \
    OperationOnPreparedStatement, NotSupportedLookup
from .statements_pool import statements_pool


DJANGO_2 = get_version().startswith('2')


def check_is_prepared(msg):
    def _check_is_prepared(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if self.prepared:
                raise OperationOnPreparedStatement(msg)
            return func(self, *args, **kwargs)
        return wrapper
    return _check_is_prepared


class PreparedQuerySet(QuerySet):
    def __init__(self, model=None, query=None, using=None, hints=None):
        super(PreparedQuerySet, self).__init__(model=model, query=query, using=using, hints=hints)
        if not query and not isinstance(self.query, ExecutePreparedQuery):
            self.query = PrepareQuery(self.model)
        self._prepare_query = None
        self.prepared = False

    def __repr__(self):
        if self.prepared:
            prepare_query = self.query.prepare_statement_sql % self.query.prepare_statement_sql_params
            arguments = self.query.prepare_params_order
            return 'PreparedQuerySet <%s (%s)>' % (prepare_query, ', '.join(arguments))
        return super(PreparedQuerySet, self).__repr__()

    @check_is_prepared('PreparedQuerySet object is not iterable')
    def __iter__(self):
        return self._base_iter()  # pragma: no cover

    @check_is_prepared('PreparedQuerySet object has no len()')
    def __len__(self):
        return super(PreparedQuerySet, self).__len__()  # pragma: no cover

    @check_is_prepared('PreparedQuerySet can\'t be fetched without calling execute method')
    def __bool__(self):
        return super(PreparedQuerySet, self).__bool__()  # pragma: no cover

    @check_is_prepared('PreparedQuerySet can\'t be fetched without calling execute method')
    def __getitem__(self, k):
        if isinstance(k, slice) and ((k.start is None or isinstance(k.start, (BindParam, int))) or
            (k.stop is None or isinstance(k.stop, (BindParam, int)))):
            if k.step:
                raise PreparedStatementException('Step isn\'t supported!')
            if isinstance(k.start, BindParam):
                k.start.field_type = BigIntegerField()
            if isinstance(k.stop, BindParam):
                k.stop.field_type = BigIntegerField()
                k.stop.set_normalize_func(
                    lambda v, values: v - (values.get(k.start.name) if isinstance(k.start, BindParam) else k.start or 0))
            qs = self.all()
            qs.query.set_limits(k.start, k.stop)
            return qs
        return super(PreparedQuerySet, self).__getitem__(k)  # pragma: no cover

    @check_is_prepared('AND not allowed on prepared statement')
    def __and__(self, other):
        return super(PreparedQuerySet, self).__and__(other)  # pragma: no cover

    @check_is_prepared('OR not allowed on prepared statement')
    def __or__(self, other):
        return super(PreparedQuerySet, self).__or__(other)  # pragma: no cover

    def _base_iter(self):
        return super(PreparedQuerySet, self).__iter__()

    def _clone(self, **kwargs):
        qs = super(PreparedQuerySet, self)._clone(**kwargs)
        qs._prepare_query = self._clone_query(PrepareQuery, self._prepare_query)
        return qs

    def _clone_query(self, klass, query=None):
        query = query or self.query
        if DJANGO_2:
            return query.chain(klass=klass)
        else:
            return query.clone(klass=klass)

    def _execute_prepare(self):
        '''
        Checks that prepare executed for the current connection and execute it if not
        '''
        connection = connections[self.db]
        name = self._prepare_query.prepare_statement_name
        if not connection.connection or name not in statements_pool[connection.connection]:
            self._prepare_query.get_prepare_compiler(self.db).execute_sql()
            statements_pool[connection.connection].append(name)

    def _set_types_for_prepare_params(self):
        '''
        Set field types for BindParams
        '''
        for filter_param, is_inner_query in get_where_nodes(self.query):
            expressions_list = filter_param.rhs
            if not isinstance(expressions_list, Sequence):
                expressions_list = [expressions_list]
            for expression in expressions_list:
                if not isinstance(expression, BindParam):
                    continue
                if type(filter_param) == IsNull:
                    raise NotSupportedLookup(
                        '%s lookup isn\'t supported in prepared statements' % filter_param.lookup_name)
                if type(filter_param) == In and not isinstance(expression, BindArray):
                    raise PreparedStatementException('Use BindArray instead of BindParam for in lookup.')
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

    def prepare(self):
        '''
        Compile prepare sql and mark qs as prepared
        '''
        self._set_types_for_prepare_params()
        self._prepare_query = self.query
        self._prepare_query.get_prepare_compiler(self.db).prepare_sql()
        self.query = self._clone_query(klass=ExecutePreparedQuery, query=self._prepare_query)
        self.query.setup_metadata(self.db)
        self.prepared = True
        return self

    def _check_execute_params(self, params):
        '''
        Check names and types for execute parameters
        '''
        if not self.prepared:
            raise QueryNotPrepared('Query isn\'t prepared!')
        if set(params.keys()) != self.query.prepare_params_names:
            raise IncorrectBindParameter('Incorrect params')
        # validate input parameters
        for prepare_param in self.query.prepare_params_by_hash.values():
            field = prepare_param.field_type
            name = prepare_param.name
            passed_param = params.get(name)
            try:
                passed_param = prepare_param.clean(passed_param)
            except ValidationError as e:
                raise e
            except:
                raise ValidationError('%s is incorrect type for %s parameter' % (passed_param, name))
            field.run_validators(passed_param)
            params[name] = passed_param
        return params

    def execute_iterator(self, **params):
        '''
        Runs execute command and prepare if needed. Returns iterator.
        '''
        params = self._check_execute_params(params)
        self._execute_prepare()
        self.query.set_prepare_params_values(params)
        self._result_cache = None
        return self._base_iter()

    def execute(self, **kwargs):
        return list(self.execute_iterator(**kwargs))

    @check_is_prepared('Iterator not allowed on prepared statement')
    def iterator(self, *args, **kwargs):
        return super(PreparedQuerySet, self).iterator(*args, **kwargs)  # pragma: no cover

    def all(self):
        if self.prepared:
            return self
        return super(PreparedQuerySet, self).all()

    @check_is_prepared('Aggregate not allowed on prepared statement')
    def aggregate(self, *args, **kwargs):
        return super(PreparedQuerySet, self).aggregate(*args, **kwargs)  # pragma: no cover

    @check_is_prepared('Count not allowed on prepared statement')
    def count(self):
        return super(PreparedQuerySet, self).count()  # pragma: no cover

    @check_is_prepared('Get not allowed on prepared statement')
    def get(self, *args, **kwargs):
        return super(PreparedQuerySet, self).get(*args, **kwargs)  # pragma: no cover

    @check_is_prepared('Create not allowed on prepared statement')
    def create(self, **kwargs):
        return super(PreparedQuerySet, self).create(**kwargs)  # pragma: no cover

    @check_is_prepared('Bulk Create not allowed on prepared statement')
    def bulk_create(self, objs, batch_size=None):
        return super(PreparedQuerySet, self).bulk_create(objs, batch_size)  # pragma: no cover

    @check_is_prepared('Get or create not allowed on prepared statement')
    def get_or_create(self, defaults=None, **kwargs):
        return super(PreparedQuerySet, self).get_or_create(defaults=defaults, **kwargs)  # pragma: no cover

    @check_is_prepared('Update or create not allowed on prepared statement')
    def update_or_create(self, defaults=None, **kwargs):
        return super(PreparedQuerySet, self).update_or_create(defaults=defaults, **kwargs)  # pragma: no cover

    @check_is_prepared('Earliest or latest not allowed on prepared statement')
    def _earliest_or_latest(self, *args, **kwargs):
        return super(PreparedQuerySet, self). \
            _earliest_or_latest(*args, **kwargs)  # pragma: no cover

    @check_is_prepared('First not allowed on prepared statement')
    def first(self):
        return super(PreparedQuerySet, self).first()  # pragma: no cover

    @check_is_prepared('Last not allowed on prepared statement')
    def last(self):
        return super(PreparedQuerySet, self).last()  # pragma: no cover

    @check_is_prepared('Operation not allowed on prepared statement')
    def in_bulk(self, *args, **kwargs):
        return super(PreparedQuerySet, self).in_bulk(*args, **kwargs)  # pragma: no cover

    @check_is_prepared('Delete not allowed on prepared statement')
    def delete(self):
        return super(PreparedQuerySet, self).delete()  # pragma: no cover

    @check_is_prepared('Update not allowed on prepared statement')
    def update(self, **kwargs):
        return super(PreparedQuerySet, self).update(**kwargs)  # pragma: no cover

    @check_is_prepared('Exists not allowed on prepared statement')
    def exists(self):
        return super(PreparedQuerySet, self).exists()  # pragma: no cover

    @check_is_prepared('Raw not allowed on prepared statement')
    def raw(self, raw_query, params=None, translations=None, using=None):
        return super(PreparedQuerySet, self).raw(raw_query, params=params,
                                                 translations=translations, using=using)  # pragma: no cover

    @check_is_prepared('Values not allowed on prepared statement')
    def values(self, *fields, **expressions):
        return super(PreparedQuerySet, self).values(*fields, **expressions)  # pragma: no cover

    @check_is_prepared('Values list not allowed on prepared statement')
    def values_list(self, *fields, **kwargs):
        return super(PreparedQuerySet, self).values_list(*fields, **kwargs)  # pragma: no cover

    @check_is_prepared('Dates not allowed on prepared statement')
    def dates(self, field_name, kind, order='ASC'):
        return super(PreparedQuerySet, self).dates(field_name, kind, order)  # pragma: no cover

    @check_is_prepared('Datetimes not allowed on prepared statement')
    def datetimes(self, field_name, kind, order='ASC', tzinfo=None):
        return super(PreparedQuerySet, self).datetimes(field_name, kind, order, tzinfo)  # pragma: no cover

    @check_is_prepared('None not allowed on prepared statement')
    def none(self):
        return super(PreparedQuerySet, self).none()  # pragma: no cover

    @check_is_prepared('Filter not allowed on prepared statement')
    def _filter_or_exclude(self, negate, *args, **kwargs):
        return super(PreparedQuerySet, self)._filter_or_exclude(negate, *args, **kwargs)  # pragma: no cover

    @check_is_prepared('Select related not allowed on prepared statement')
    def select_related(self, *fields):
        return super(PreparedQuerySet, self).select_related(*fields)  # pragma: no cover

    @check_is_prepared('Prefetch related not allowed on prepared statement')
    def prefetch_related(self, *lookups):
        return super(PreparedQuerySet, self).prefetch_related(*lookups)  # pragma: no cover

    @check_is_prepared('Annotate not allowed on prepared statement')
    def annotate(self, *args, **kwargs):
        return super(PreparedQuerySet, self).annotate(*args, **kwargs)  # pragma: no cover

    @check_is_prepared('Order by not allowed on prepared statement')
    def order_by(self, *field_names):
        return super(PreparedQuerySet, self).order_by(*field_names)  # pragma: no cover

    @check_is_prepared('Distinct not allowed on prepared statement')
    def distinct(self, *field_names):
        return super(PreparedQuerySet, self).distinct(*field_names)  # pragma: no cover

    @check_is_prepared('Extra not allowed on prepared statement')
    def extra(self, select=None, where=None, params=None, tables=None,
              order_by=None, select_params=None):
        return super(PreparedQuerySet, self).extra(select, where, params, tables,
                                                   order_by, select_params)  # pragma: no cover

    @check_is_prepared('Reverse not allowed on prepare statement')
    def reverse(self):
        return super(PreparedQuerySet, self).reverse()  # pragma: no cover

    @check_is_prepared('Defer not allowed on prepare statement')
    def defer(self, *fields):
        return super(PreparedQuerySet, self).defer(*fields)  # pragma: no cover

    @check_is_prepared('Only not allowed on prepare statement')
    def only(self, *fields):
        return super(PreparedQuerySet, self).only(*fields)  # pragma: no cover

    @check_is_prepared('Using not allowed on prepare statement')
    def using(self, alias):
        return super(PreparedQuerySet, self).using(alias)  # pragma: no cover
