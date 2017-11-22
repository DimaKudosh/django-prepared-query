from django.db.models.manager import BaseManager
from .queryset import PreparedQuerySet


class PreparedManager(BaseManager.from_queryset(PreparedQuerySet)):
    pass
