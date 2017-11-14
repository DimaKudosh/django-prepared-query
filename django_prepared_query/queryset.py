from collections import Sequence
from django.db.models import QuerySet, Model
from django.db import connections
from django.db.models.lookups import IsNull, In
from django.core.exceptions import ValidationError
from .query import PrepareQuery, ExecutePrepareQuery
from .params import BindParam
from .utils import get_where_nodes
from .exceptions import PreparedStatementException, QueryNotPrepared, IncorrectBindParameter, \
    OperationOnPreparedStatement, NotSupportedLookup


class PrepareQuerySet(QuerySet):
    def __init__(self, model=None, query=None, using=None, hints=None):
        super(PrepareQuerySet, self).__init__(model=model, query=query, using=using, hints=hints)
        if not query and not isinstance(self.query, ExecutePrepareQuery):
            self.query = PrepareQuery(self.model)
        self.prepared = False
        self.prepare_placeholders = []

    def __repr__(self):
        if self.prepared:
            prepare_query = self.query.prepare_statement_sql % self.query.prepare_statement_sql_params
            arguments = self.query.prepare_params_order
            return 'PrepareQuerySet <%s (%s)>' % (prepare_query, ', '.join(arguments))
        return super(PrepareQuerySet, self).__repr__()

    def __iter__(self):
        self._check_prepared('PreparedQuerySet object is not iterable')
        return self._base_iter()  # pragma: no cover

    def __len__(self):
        self._check_prepared('PreparedQuerySet object has no len()')
        return super(PrepareQuerySet, self).__len__()  # pragma: no cover

    def __bool__(self):
        self._check_prepared('PreparedQuerySet can\'t be fetched without calling execute method')
        return super(PrepareQuerySet, self).__bool__()  # pragma: no cover

    def __getitem__(self, item):
        self._check_prepared('PreparedQuerySet can\'t be fetched without calling execute method')
        return super(PrepareQuerySet, self).__getitem__(item)  # pragma: no cover

    def __and__(self, other):
        self._check_prepared('AND not allowed on prepared statement')
        return super(PrepareQuerySet, self).__and__(other)  # pragma: no cover

    def __or__(self, other):
        self._check_prepared('OR not allowed on prepared statement')
        return super(PrepareQuerySet, self).__or__(other)  # pragma: no cover

    def _base_iter(self):
        return super(PrepareQuerySet, self).__iter__()

    def _check_prepared(self, msg):
        if self.prepared:
            raise OperationOnPreparedStatement(msg)

    def _execute_prepare(self):
        connection = connections[self.db]
        query = self.query
        name = query.prepare_statement_name
        prepared_statements = getattr(connection, 'prepared_statements', None)
        if prepared_statements is None:
            prepared_statements = {}
        if name not in prepared_statements or prepared_statements[name] != connection.connection:
            query = query.clone(klass=PrepareQuery)
            query.get_prepare_compiler(self.db).execute_sql()
            prepared_statements[name] = connection.connection
            setattr(connection, 'prepared_statements', prepared_statements)
        self.query = query.clone(klass=ExecutePrepareQuery)
        return self

    def prepare(self):
        assert self.query.can_filter(), 'Cannot prepare a query once a slice has been taken.'
        for filter_param in get_where_nodes(self.query):
            if isinstance(filter_param, (IsNull, In)):
                raise NotSupportedLookup('%s lookup isn\'t supported in prepared statements' % filter_param.lookup_name)
            expressions_list = filter_param.rhs
            if not isinstance(expressions_list, Sequence):
                expressions_list = [expressions_list]
            for expression in expressions_list:
                if not isinstance(expression, BindParam):
                    continue
                prepare_param = self.query.prepare_params_by_name[expression.name]
                if not prepare_param.field_type:
                    prepare_param.field_type = filter_param.lhs.output_field
        for name, prepare_param in self.query.prepare_params_by_name.items():
            if not prepare_param.field_type:
                raise PreparedStatementException('Field type is required for %s' % name)
        query = self.query.clone(klass=PrepareQuery)
        query.get_prepare_compiler(self.db).prepare_sql()
        self.query = query
        self.prepared = True
        return self

    def execute(self, **kwargs):
        if not self.prepared:
            raise QueryNotPrepared('Prepare statement not created!')
        params = set(kwargs.keys())
        prepare_params = set(self.query.prepare_params_order)
        if params != prepare_params:
            raise IncorrectBindParameter('Incorrect params')
        for key, val in kwargs.items():
            field = self.query.prepare_params_by_name[key].field_type
            if isinstance(val, Model):
                val = val._get_pk_val()
            try:
                val = field.get_prep_value(val)
            except:
                raise ValidationError('%s is incorrect type for %s parameter' % (val, key))
            field.run_validators(val)
            kwargs[key] = val
        self._execute_prepare()
        self.query.prepare_params_values = kwargs
        qs = self._clone()
        return list(qs._base_iter())

    def iterator(self):
        self._check_prepared('Iterator not allowed on prepared statement')
        return super(PrepareQuerySet, self).iterator()  # pragma: no cover

    def aggregate(self, *args, **kwargs):
        self._check_prepared('Aggregate not allowed on prepared statement')
        return super(PrepareQuerySet, self).aggregate(*args, **kwargs)  # pragma: no cover

    def count(self):
        self._check_prepared('Count not allowed on prepared statement')
        return super(PrepareQuerySet, self).count()  # pragma: no cover

    def get(self, *args, **kwargs):
        self._check_prepared('Get not allowed on prepared statement')
        return super(PrepareQuerySet, self).get(*args, **kwargs)  # pragma: no cover

    def create(self, **kwargs):
        self._check_prepared('Create not allowed on prepared statement')
        return super(PrepareQuerySet, self).create(**kwargs)  # pragma: no cover

    def bulk_create(self, objs, batch_size=None):
        self._check_prepared('Bulk Create not allowed on prepared statement')
        return super(PrepareQuerySet, self).bulk_create(objs, batch_size)  # pragma: no cover

    def get_or_create(self, defaults=None, **kwargs):
        self._check_prepared('Get or create not allowed on prepared statement')
        return super(PrepareQuerySet, self).get_or_create(defaults=defaults, **kwargs)  # pragma: no cover

    def update_or_create(self, defaults=None, **kwargs):
        self._check_prepared('Update or create not allowed on prepared statement')
        return super(PrepareQuerySet, self).update_or_create(defaults=defaults, **kwargs)  # pragma: no cover

    def _earliest_or_latest(self, field_name=None, direction="-"):
        self._check_prepared('Earliest or latest not allowed on prepared statement')
        return super(PrepareQuerySet, self).\
            _earliest_or_latest(field_name=field_name, direction=direction)  # pragma: no cover

    def first(self):
        self._check_prepared('First not allowed on prepared statement')
        return super(PrepareQuerySet, self).first()  # pragma: no cover

    def last(self):
        self._check_prepared('Last not allowed on prepared statement')
        return super(PrepareQuerySet, self).last()  # pragma: no cover

    def in_bulk(self, id_list=None):
        self._check_prepared('Operation not allowed on prepared statement')
        return super(PrepareQuerySet, self).in_bulk(id_list=id_list)  # pragma: no cover

    def delete(self):
        self._check_prepared('Delete not allowed on prepared statement')
        return super(PrepareQuerySet, self).delete()  # pragma: no cover

    def update(self, **kwargs):
        self._check_prepared('Update not allowed on prepared statement')
        return super(PrepareQuerySet, self).update(**kwargs)  # pragma: no cover

    def exists(self):
        self._check_prepared('Exists not allowed on prepared statement')
        return super(PrepareQuerySet, self).exists()  # pragma: no cover

    def raw(self, raw_query, params=None, translations=None, using=None):
        self._check_prepared('Raw not allowed on prepared statement')
        return super(PrepareQuerySet, self).raw(raw_query, params=params,
                                                translations=translations, using=using)  # pragma: no cover

    def values(self, *fields, **expressions):
        self._check_prepared('Values not allowed on prepared statement')
        return super(PrepareQuerySet, self).values(*fields, **expressions)  # pragma: no cover

    def values_list(self, *fields, **kwargs):
        self._check_prepared('Values list not allowed on prepared statement')
        return super(PrepareQuerySet, self).values_list(*fields, **kwargs)  # pragma: no cover

    def dates(self, field_name, kind, order='ASC'):
        self._check_prepared('Dates not allowed on prepared statement')
        return super(PrepareQuerySet, self).dates(field_name, kind, order)  # pragma: no cover

    def datetimes(self, field_name, kind, order='ASC', tzinfo=None):
        self._check_prepared('Datetimes not allowed on prepared statement')
        return super(PrepareQuerySet, self).datetimes(field_name, kind, order, tzinfo)  # pragma: no cover

    def none(self):
        self._check_prepared('None not allowed on prepared statement')
        return super(PrepareQuerySet, self).none()  # pragma: no cover

    def all(self):
        self._check_prepared('All not allowed on prepared statement')
        return super(PrepareQuerySet, self).all()  # pragma: no cover

    def _filter_or_exclude(self, negate, *args, **kwargs):
        self._check_prepared('Filter not allowed on prepared statement')
        return super(PrepareQuerySet, self)._filter_or_exclude(negate, *args, **kwargs)  # pragma: no cover

    def select_related(self, *fields):
        self._check_prepared('Select related not allowed on prepared statement')
        return super(PrepareQuerySet, self).select_related(*fields)  # pragma: no cover

    def prefetch_related(self, *lookups):
        self._check_prepared('Prefetch related not allowed on prepared statement')
        return super(PrepareQuerySet, self).prefetch_related(*lookups)  # pragma: no cover

    def annotate(self, *args, **kwargs):
        self._check_prepared('Annotate not allowed on prepared statement')
        return super(PrepareQuerySet, self).annotate(*args, **kwargs)  # pragma: no cover

    def order_by(self, *field_names):
        self._check_prepared('Order by not allowed on prepared statement')
        return super(PrepareQuerySet, self).order_by(*field_names)  # pragma: no cover

    def distinct(self, *field_names):
        self._check_prepared('Distinct not allowed on prepared statement')
        return super(PrepareQuerySet, self).distinct(*field_names)  # pragma: no cover

    def extra(self, select=None, where=None, params=None, tables=None,
              order_by=None, select_params=None):
        self._check_prepared('Extra not allowed on prepared statement')
        return super(PrepareQuerySet, self).extra(select, where, params, tables,
                                                  order_by, select_params)  # pragma: no cover

    def reverse(self):
        self._check_prepared('Reverse not allowed on prepare statement')
        return super(PrepareQuerySet, self).reverse()  # pragma: no cover

    def defer(self, *fields):
        self._check_prepared('Defer not allowed on prepare statement')
        return super(PrepareQuerySet, self).defer(*fields)  # pragma: no cover

    def only(self, *fields):
        self._check_prepared('Only not allowed on prepare statement')
        return super(PrepareQuerySet, self).only(*fields)  # pragma: no cover

    def using(self, alias):
        self._check_prepared('Using not allowed on prepare statement')
        return super(PrepareQuerySet, self).using(alias)  # pragma: no cover
