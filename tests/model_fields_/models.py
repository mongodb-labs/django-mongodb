from django.db import models

from django_mongodb_backend.fields import ObjectIdField


class ObjectIdModel(models.Model):
    field = ObjectIdField()


class NullableObjectIdModel(models.Model):
    field = ObjectIdField(blank=True, null=True)


class PrimaryKeyObjectIdModel(models.Model):
    field = ObjectIdField(primary_key=True)
