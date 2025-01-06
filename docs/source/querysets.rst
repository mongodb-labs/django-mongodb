``QuerySet`` API reference
==========================

Some MongoDB-specific ``QuerySet`` methods are available by adding a custom
:class:`~django.db.models.Manager`, ``MongoManager``, to your model::

    from django.db import models

    from django_mongodb_backend.managers import MongoManager


    class MyModel(models.Model):
        ...

        objects = MongoManager()


.. currentmodule:: django_mongodb_backend.queryset.MongoQuerySet

``raw_aggregate()``
-------------------

.. method:: raw_aggregate(pipeline, using=None)

Similar to :meth:`QuerySet.raw()<django.db.models.query.QuerySet.raw>`, but
instead of a raw SQL query, this method accepts a pipeline that will be passed
to :meth:`pymongo.collection.Collection.aggregate`.

For example, you could write a custom match criteria::

    Question.objects.raw_aggregate([{"$match": {"question_text": "What's up"}}])

The pipeline may also return additional fields that will be added as
annotations on the models::

    >>> questions = Question.objects.raw_aggregate([{
    ...     "$project": {
    ...         "question_text": 1,
    ...         "pub_date": 1,
    ...         "year_published": {"$year": "$pub_date"}
    ...     }
    ... }])
    >>> for q in questions:
    ...     print(f"{q.question_text} was published in {q.year_published}.")
    ...
    What's up? was published in 2024.

Fields may also be left out:

    >>> Question.objects.raw_aggregate([{"$project": {"question_text": 1}}])

The ``Question`` objects returned by this query will be deferred model instances
(see :meth:`~django.db.models.query.QuerySet.defer()`). This means that the
fields that are omitted from the query will be loaded on demand. For example::

    >>> for q in Question.objects.raw_aggregate([{"$project": {"question_text": 1}}]):
    >>>     print(
    ...         q.question_text,  # This will be retrieved by the original query.
    ...         q.pub_date,       # This will be retrieved on demand.
    ...     )
    ...
    What's new 2023-09-03 12:00:00+00:00
    What's up 2024-08-23 20:57:30+00:00

From outward appearances, this looks like the query has retrieved both the
question text and published date. However, this example actually issued three
queries. Only the question texts were retrieved by the ``raw_aggregate()``
query -- the published dates were both retrieved on demand when they were
printed.
