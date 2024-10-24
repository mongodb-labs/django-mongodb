from django.db.models.manager import BaseManager
from .query import MongoQuerySet


class MongoManager(BaseManager.from_queryset(MongoQuerySet)):
    pass
