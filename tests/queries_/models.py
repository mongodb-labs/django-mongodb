from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=10)

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=10)
    author = models.ForeignKey(Author, models.CASCADE)

    def __str__(self):
        return self.title
