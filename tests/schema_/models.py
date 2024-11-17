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
    unique_together_one = models.CharField(max_length=10)
    unique_together_two = models.CharField(max_length=10)

    class Meta:
        apps = new_apps
        unique_together = [("unique_together_one", "unique_together_two")]


class Author(models.Model):
    name = models.CharField(max_length=10)
    age = models.IntegerField(db_index=True)
    address = EmbeddedModelField(Address)
    employee_id = models.IntegerField(unique=True)
    unique_together_three = models.CharField(max_length=10)
    unique_together_four = models.CharField(max_length=10)

    class Meta:
        apps = new_apps
        unique_together = [("unique_together_three", "unique_together_four")]


class Book(models.Model):
    name = models.CharField(max_length=100)
    author = EmbeddedModelField(Author)

    class Meta:
        apps = new_apps
