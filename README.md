# MongoDB backend for Django

This backend is in the pre-alpha stage of development. Backwards incompatible
changes may be made without notice. We welcome your feedback as we continue to
explore and build.

## Install and usage

The development version of this package supports Django 5.0.x. To install it:

`pip install git+https://github.com/mongodb-labs/django-mongodb`

Configure the Django `DATABASES` setting similar to this:

```python
DATABASES = {
    "default": {
        "ENGINE": "django_mongodb",
        "NAME": "my_database",
        "USER": "my_user",
        "PASSWORD": "my_password",
        "OPTIONS": {...},
    },
}
```

`OPTIONS` is an optional dictionary of parameters that will be passed to
[`MongoClient`](https://pymongo.readthedocs.io/en/stable/api/pymongo/mongo_client.html).

In your Django settings, you must specify that all models should use
`ObjectIdAutoField`.

```python
DEFAULT_AUTO_FIELD = "django_mongodb.fields.ObjectIdAutoField"
```

This won't override any apps that have an `AppConfig` that specifies
`default_auto_field`. For those apps, you'll need to create a custom
`AppConfig`.

For example, you might create `mysite/apps.py` like this:

```python
from django.contrib.admin.apps import AdminConfig
from django.contrib.auth.apps import AuthConfig
from django.contrib.contenttypes.apps import ContentTypesConfig


class MongoAdminConfig(AdminConfig):
    default_auto_field = "django_mongodb.fields.ObjectIdAutoField"


class MongoAuthConfig(AuthConfig):
    default_auto_field = "django_mongodb.fields.ObjectIdAutoField"


class MongoContentTypesConfig(ContentTypesConfig):
    default_auto_field = "django_mongodb.fields.ObjectIdAutoField"
```

Then replace each app reference in the `INSTALLED_APPS` setting with the new
``AppConfig``. For example, replace  `'django.contrib.admin'` with
`'mysite.apps.MongoAdminConfig'`.

Because all models must use `ObjectIdAutoField`, each third-party and contrib app
you use needs to have its own migrations specific to MongoDB.

For example, you might configure your settings like this:

```python
MIGRATION_MODULES = {
    "admin": "mongo_migrations.admin",
    "auth": "mongo_migrations.auth",
    "contenttypes": "mongo_migrations.contenttypes",
}
```

After creating a `mongo_migrations` directory, you can then run:

```console
$ python manage.py makemigrations admin auth contenttypes
Migrations for 'admin':
  mongo_migrations/admin/0001_initial.py
    - Create model LogEntry
...
```

And whenever you run `python manage.py startapp`, you must remove the line:

`default_auto_field = 'django.db.models.BigAutoField'`

from the new application's `apps.py` file.

## Notes on Django QuerySets

* `QuerySet.explain()` supports the [`comment` and `verbosity` options](
  https://www.mongodb.com/docs/manual/reference/command/explain/#command-fields).

   Example: `QuerySet.explain(comment="...", verbosity="...")`

   Valid values for `verbosity` are `"queryPlanner"` (default),
   `"executionStats"`, and `"allPlansExecution"`.

## Why are we building a MongoDB-Django integration?

Building a robust solution that makes Django and NoSQL databases work together well has historically been challenging due to Django's ORM being built around relational database principles. While there have been several attempts in the past to create NoSQL (and MongoDB) integrations for Django, many of these projects have not achieved lasting success for various reasons. So, why have we chosen to tackle this problem now?

According to the 2023 Django Developer Survey, 8% of respondents reported using MongoDB as a database backend with Django. This figure has shown a consistent upward trend in recent years (see 2021 and 2022 surveys). Additionally, numerous community members and customers have expressed a strong interest in leveraging Django alongside MongoDB.
Our goal is to meet the needs of the developer community by providing an exceptional experience when working with MongoDB. Therefore, we are embarking on this journey to create a reliable integration. **Please note that the current project is in a very early stage of development and is not yet ready for PoC or Production use cases.**

## Current capabilities

At this stage, the project should let you replicate the djangoproject.com tutorial with minimal changes. You will likely be able to run it passing a portion of the standard Django test suite but not all of it. Some key features that we have added so far are:
- Able to define MongoDB collections using Django models
- Able to query data using Django’s `QuerySets`
- Able to use Django’s authentication system `django.contrib.auth`
- Able to use Django’s automatic admin interface `django.contrib.admin`
- Able to use Django’s management commands
- Able to use MongoDB’s Aggregation Pipeline

## What's next?
We are working towards a Public Preview release early 2025. We do not yet have a timeline for general availability. Exact details of the roadmap will be published soon. Stay tuned! 
What level of support will MongoDB provide to developers using this code?

This code is still in development and not intended for POC or production use cases, so we are not providing formal support within our Technical Services team at this time. 

## Known issues and limitations

- The following `QuerySet` methods aren't supported:
  - `bulk_update()`
  - `dates()`
  - `datetimes()`
  - `distinct()`
  - `extra()`
  - `prefetch_related()`

- `QuerySet.delete()` and `update()` do not support queries that span multiple
  collections.

- `Subquery`, `Exists`, and using a `QuerySet` in `QuerySet.annotate()` aren't
  supported.

- `DateTimeField` doesn't support microsecond precision, and correspondingly,
  `DurationField` stores milliseconds rather than microseconds.

- The following database functions aren't supported:
    - `Chr`
    - `ExtractQuarter`
    - `MD5`
    - `Now`
    - `Ord`
    - `Pad`
    - `Repeat`
    - `Reverse`
    - `Right`
    - `SHA1`, `SHA224`, `SHA256`, `SHA384`, `SHA512`
    - `Sign`
    - `TruncDate`
    - `TruncTime`

- The `tzinfo` parameter of the `Trunc` database functions doesn't work
  properly because MongoDB converts the result back to UTC.

- When querying `JSONField`:
  - There is no way to distinguish between a JSON "null" (represented by
    `Value(None, JSONField())`) and a SQL null (queried using the `isnull`
    lookup). Both of these queries return both of these nulls.
  - Some queries with `Q` objects, e.g. `Q(value__foo="bar")`, don't work
    properly, particularly with `QuerySet.exclude()`.
  - Filtering for a `None` key, e.g. `QuerySet.filter(value__j=None)`
    incorrectly returns objects where the key doesn't exist.
  - You can study the skipped tests in `DatabaseFeatures.django_test_skips` for
    more details on known issues.


## We value your feedback!
We invite you to share your feedback as we work to address this challenge. If you are interested in becoming a design partner, please connect with us through our community forum. You can also create issues or submit pull requests directly to our project GitHub repository.

## Troubleshooting

TODO