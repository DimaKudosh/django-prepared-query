from django.db.models.manager import BaseManager
from .queryset import PrepareQuerySet


class PrepareManager(BaseManager.from_queryset(PrepareQuerySet)):
    pass
