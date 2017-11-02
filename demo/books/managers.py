from django.db import models
from django_prepared_query import PrepareManager, BindParam


class PublisherManager(models.Manager):
    def get_by_id(self, id):
        return self.get_queryset().get(id=id)


class PreparePublisherManager(PrepareManager):
    def get_by_id(self, id):
        prepared_publisher_by_id = getattr(self, 'prepared_publisher_by_id', None)
        if prepared_publisher_by_id is None:
            prepared_publisher_by_id = self.get_queryset().filter(id=BindParam('id')).prepare()
            setattr(self, 'prepared_publisher_by_id', prepared_publisher_by_id)
        return prepared_publisher_by_id.execute(id=id)[0]
