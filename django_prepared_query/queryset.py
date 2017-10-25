from collections import Sequence
from django.db.models import QuerySet, Model
from django.db import connections
from django.db.models.lookups import IsNull, In
from django.core.exceptions import ValidationError
from .query import PrepareQuery, ExecutePrepareQuery
from .params import BindParam
from .utils import generate_random_string, get_where_nodes
from .exceptions import PreparedStatementException, QueryNotPrepared, IncorrectBindParameter, \
    OperationOnPreparedStatement, NotSupportedLookup


class PrepareQuerySet(QuerySet):
    HASH_LENGTH = 20

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
        if self.prepared:
            raise OperationOnPreparedStatement('PreparedQuerySet object is not iterable')
        return self._base_iter()

    def __len__(self):
        if self.prepared:
            raise OperationOnPreparedStatement('PreparedQuerySet object has no len()')
        return super(PrepareQuerySet, self).__len__()

    def __bool__(self):
        if self.prepared:
            raise OperationOnPreparedStatement('PreparedQuerySet can\'t be fetched without calling execute method')
        return super(PrepareQuerySet, self).__bool__()

    def __getitem__(self, item):
        if self.prepared:
            raise OperationOnPreparedStatement('PreparedQuerySet can\'t be fetched without calling execute method')
        return super(PrepareQuerySet, self).__getitem__(item)

    def __and__(self, other):
        if self.prepared:
            raise OperationOnPreparedStatement('AND not allowed on prepared statement')
        return super(PrepareQuerySet, self).__and__(other)

    def __or__(self, other):
        if self.prepared:
            raise OperationOnPreparedStatement('OR not allowed on prepared statement')
        return super(PrepareQuerySet, self).__or__(other)

    def _base_iter(self):
        return super(PrepareQuerySet, self).__iter__()

    def _generate_prepare_statement_name(self):
        return '%s_%s' % (self.model._meta.model_name, generate_random_string(self.HASH_LENGTH))

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
        query.set_prepare_statement_name(self._generate_prepare_statement_name())
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
        if self.prepared:
            raise OperationOnPreparedStatement('Iterator not allowed on prepared statement')
        return super(PrepareQuerySet, self).iterator()

    def aggregate(self, *args, **kwargs):
        if self.prepared:
            raise OperationOnPreparedStatement('Aggregate not allowed on prepared statement')
        return super(PrepareQuerySet, self).aggregate(*args, **kwargs)

    def count(self):
        if self.prepared:
            raise OperationOnPreparedStatement('Count not allowed on prepared statement')
        return super(PrepareQuerySet, self).count()

    def get(self, *args, **kwargs):
        if self.prepared:
            raise OperationOnPreparedStatement('Get not allowed on prepared statement')
        return super(PrepareQuerySet, self).get(*args, **kwargs)

    def create(self, **kwargs):
        if self.prepared:
            raise OperationOnPreparedStatement('Create not allowed on prepared statement')
        return super(PrepareQuerySet, self).create(**kwargs)

    def bulk_create(self, objs, batch_size=None):
        if self.prepared:
            raise OperationOnPreparedStatement('Bulk Create not allowed on prepared statement')
        return super(PrepareQuerySet, self).bulk_create(objs, batch_size)

    def get_or_create(self, defaults=None, **kwargs):
        if self.prepared:
            raise OperationOnPreparedStatement('Get or create not allowed on prepared statement')
        return super(PrepareQuerySet, self).get_or_create(defaults=defaults, **kwargs)

    def update_or_create(self, defaults=None, **kwargs):
        if self.prepared:
            raise OperationOnPreparedStatement('Update or create not allowed on prepared statement')
        return super(PrepareQuerySet, self).update_or_create(defaults=defaults, **kwargs)

    def _earliest_or_latest(self, field_name=None, direction="-"):
        if self.prepared:
            raise OperationOnPreparedStatement('Earliest or latest not allowed on prepared statement')
        return super(PrepareQuerySet, self)._earliest_or_latest(field_name=field_name, direction=direction)

    def first(self):
        if self.prepared:
            raise OperationOnPreparedStatement('First not allowed on prepared statement')
        return super(PrepareQuerySet, self).first()

    def last(self):
        if self.prepared:
            raise OperationOnPreparedStatement('Last not allowed on prepared statement')
        return super(PrepareQuerySet, self).last()

    def in_bulk(self, id_list=None):
        if self.prepared:
            raise OperationOnPreparedStatement('Operation not allowed on prepared statement')
        return super(PrepareQuerySet, self).in_bulk(id_list=id_list)

    def delete(self):
        if self.prepared:
            raise OperationOnPreparedStatement('Delete not allowed on prepared statement')
        return super(PrepareQuerySet, self).delete()

    def update(self, **kwargs):
        if self.prepared:
            raise OperationOnPreparedStatement('Update not allowed on prepared statement')
        return super(PrepareQuerySet, self).update(**kwargs)

    def exists(self):
        if self.prepared:
            raise OperationOnPreparedStatement('Exists not allowed on prepared statement')
        return super(PrepareQuerySet, self).exists()

    def raw(self, raw_query, params=None, translations=None, using=None):
        if self.prepared:
            raise OperationOnPreparedStatement('Raw not allowed on prepared statement')
        return super(PrepareQuerySet, self).raw(raw_query, params=params, translations=translations, using=using)

    def values(self, *fields, **expressions):
        if self.prepared:
            raise OperationOnPreparedStatement('Values not allowed on prepared statement')
        return super(PrepareQuerySet, self).values(*fields, **expressions)

    def values_list(self, *fields, **kwargs):
        if self.prepared:
            raise OperationOnPreparedStatement('Values list not allowed on prepared statement')
        return super(PrepareQuerySet, self).values_list(*fields, **kwargs)

    def dates(self, field_name, kind, order='ASC'):
        if self.prepared:
            raise OperationOnPreparedStatement('Dates not allowed on prepared statement')
        return super(PrepareQuerySet, self).dates(field_name, kind, order)

    def datetimes(self, field_name, kind, order='ASC', tzinfo=None):
        if self.prepared:
            raise OperationOnPreparedStatement('Datetimes not allowed on prepared statement')
        return super(PrepareQuerySet, self).datetimes(field_name, kind, order, tzinfo)

    def none(self):
        if self.prepared:
            raise OperationOnPreparedStatement('None not allowed on prepared statement')
        return super(PrepareQuerySet, self).none()

    def all(self):
        if self.prepared:
            raise OperationOnPreparedStatement('All not allowed on prepared statement')
        return super(PrepareQuerySet, self).all()

    def _filter_or_exclude(self, negate, *args, **kwargs):
        if self.prepared:
            raise OperationOnPreparedStatement('Filter not allowed on prepared statement')
        return super(PrepareQuerySet, self)._filter_or_exclude(negate, *args, **kwargs)

    def select_related(self, *fields):
        if self.prepared:
            raise OperationOnPreparedStatement('Select related not allowed on prepared statement')
        return super(PrepareQuerySet, self).select_related(*fields)

    def prefetch_related(self, *lookups):
        if self.prepared:
            raise OperationOnPreparedStatement('Prefetch related not allowed on prepared statement')
        return super(PrepareQuerySet, self).prefetch_related(*lookups)

    def annotate(self, *args, **kwargs):
        if self.prepared:
            raise OperationOnPreparedStatement('Annotate not allowed on prepared statement')
        return super(PrepareQuerySet, self).annotate(*args, **kwargs)

    def order_by(self, *field_names):
        if self.prepared:
            raise OperationOnPreparedStatement('Order by not allowed on prepared statement')
        return super(PrepareQuerySet, self).order_by(*field_names)

    def distinct(self, *field_names):
        if self.prepared:
            raise OperationOnPreparedStatement('Distinct not allowed on prepared statement')
        return super(PrepareQuerySet, self).distinct(*field_names)

    def extra(self, select=None, where=None, params=None, tables=None,
              order_by=None, select_params=None):
        if self.prepared:
            raise OperationOnPreparedStatement('Extra not allowed on prepared statement')
        return super(PrepareQuerySet, self).extra(select, where, params, tables, order_by, select_params)

    def reverse(self):
        if self.prepared:
            raise OperationOnPreparedStatement('Reverse not allowed on prepare statement')
        return super(PrepareQuerySet, self).reverse()

    def defer(self, *fields):
        if self.prepared:
            raise OperationOnPreparedStatement('Defer not allowed on prepare statement')
        return super(PrepareQuerySet, self).defer(*fields)

    def only(self, *fields):
        if self.prepared:
            raise OperationOnPreparedStatement('Only not allowed on prepare statement')
        return super(PrepareQuerySet, self).only(*fields)

    def using(self, alias):
        if self.prepared:
            raise OperationOnPreparedStatement('Using not allowed on prepare statement')
        return super(PrepareQuerySet, self).using(alias)
