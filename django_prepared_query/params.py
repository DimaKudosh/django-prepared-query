import random
from itertools import repeat
from django.core.exceptions import ValidationError
from django.db.models import Expression, Model


class BindParam(Expression):
    def __init__(self, name, field_type=None):
        super(BindParam, self).__init__(None)
        self.name = name
        self.field_type = field_type
        if self.field_type:
            self.field_type.validators = []  # Disable validation for user specified field types
            if not self.field_type.max_length:
                self.field_type.max_length = 256
        self.hash = '%032x' % random.getrandbits(128)
        self.size = 1

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.name)

    def as_sql(self, compiler, connection):
        return '{}', [self.hash]

    def resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False):
        c = super(BindParam, self).resolve_expression(query, allow_joins, reuse, summarize, for_save)
        query.add_prepare_param(self)
        return c

    def get_group_by_cols(self):
        return []

    def clean(self, value):
        if isinstance(value, Model):
            value = value._get_pk_val()
        return self.field_type.get_prep_value(value)


class BindArray(BindParam):
    def __init__(self, name, size, field_type=None):
        super().__init__(name, field_type)
        self.size = size

    def as_sql(self, compiler, connection):
        return ','.join(repeat('{}', self.size)), [self.hash]

    def clean(self, value):
        total_items = len(value)
        if total_items > self.size:
            raise ValidationError('%s param should have max %d items. Got %d' % (self.name, self.size, total_items))
        cleaned_params = [self.field_type.get_prep_value(param) for param in value]
        cleaned_params = cleaned_params + [None] * (self.size - total_items)
        return cleaned_params
