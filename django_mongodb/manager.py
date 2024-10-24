from django.db.models.manager import BaseManager
from .query import MongoQuerySet


class MongoManager(BaseManager.from_queryset(MongoQuerySet)):
    def get_query_set(self):
        return MongoQuerySet(self.model, using=self._db)
