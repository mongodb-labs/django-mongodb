from django.apps.registry import Apps
from django.db import models

from django_mongodb.fields import EmbeddedModelField

# Because we want to test creation and deletion of these as separate things,
# these models are all inserted into a separate Apps so the main test
# runner doesn't migrate them.

new_apps = Apps()


class Address(models.Model):
    city = models.CharField(max_length=20)
    state = models.CharField(max_length=2)
    zip_code = models.IntegerField(db_index=True)
    uid = models.IntegerField(unique=True)

    class Meta:
        apps = new_apps


class Author(models.Model):
    name = models.CharField(max_length=10)
    age = models.IntegerField(db_index=True)
    address = EmbeddedModelField(Address)
    employee_id = models.IntegerField(unique=True)

    class Meta:
        apps = new_apps


class Book(models.Model):
    name = models.CharField(max_length=100)
    author = EmbeddedModelField(Author)

    class Meta:
        apps = new_apps