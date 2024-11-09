from django.db import models

from django_mongodb.fields import EmbeddedModelField, ObjectIdField


# ObjectIdField
class ObjectIdModel(models.Model):
    field = ObjectIdField()


class NullableObjectIdModel(models.Model):
    field = ObjectIdField(blank=True, null=True)


class PrimaryKeyObjectIdModel(models.Model):
    field = ObjectIdField(primary_key=True)


# EmbeddedModelField
class Target(models.Model):
    index = models.IntegerField()


class DecimalModel(models.Model):
    decimal = models.DecimalField(max_digits=9, decimal_places=2)


class DecimalKey(models.Model):
    decimal = models.DecimalField(max_digits=9, decimal_places=2, primary_key=True)


class DecimalParent(models.Model):
    child = models.ForeignKey(DecimalKey, models.CASCADE)


class EmbeddedModelFieldModel(models.Model):
    simple = EmbeddedModelField("EmbeddedModel", null=True, blank=True)
    decimal_parent = EmbeddedModelField(DecimalParent, null=True, blank=True)


class EmbeddedModel(models.Model):
    some_relation = models.ForeignKey(Target, models.CASCADE, null=True, blank=True)
    someint = models.IntegerField(db_column="custom_column")
    auto_now = models.DateTimeField(auto_now=True)
    auto_now_add = models.DateTimeField(auto_now_add=True)


class Address(models.Model):
    city = models.CharField(max_length=20)
    state = models.CharField(max_length=2)


class Author(models.Model):
    name = models.CharField(max_length=10)
    age = models.IntegerField()
    address = EmbeddedModelField(Address)


class Book(models.Model):
    name = models.CharField(max_length=100)
    author = EmbeddedModelField(Author)
