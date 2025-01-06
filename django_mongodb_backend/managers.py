from django.db.models.manager import BaseManager

from .queryset import MongoQuerySet


class MongoManager(BaseManager.from_queryset(MongoQuerySet)):
    pass
