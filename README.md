# MongoDB backend for Django

This backend is in the pre-alpha stage of development. Backwards incompatible
changes may be made without notice. We welcome your feedback as we continue to
explore and build.

## Install and usage

Use the version of `django-mongodb` that corresponds to your version of
Django. For example, to get the latest compatible release for Django 5.0.x:

`pip install django-mongodb==5.0.*`

The minor release number of Django doesn't correspond to the minor release
number of django-mongodb. Use the latest minor release of each.

While django-mongodb only has pre-releases (alphas or betas), you'll see an
error with a list of the available versions. In that case, include `--pre` to
allow `pip` to install the latest pre-release.

For example, if django-mongodb 5.0 alpha 1 is the latest available version
of the 5.0 release series:

```
$ pip install django-mongodb==5.0.*
ERROR: Could not find a version that satisfies the requirement
django-mongodb==5.0.* (from versions: ..., 5.0a1)

$ pip install --pre django-mongodb==5.0.*
...
Successfully installed ... django-mongodb-5.0a1 ...
```

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
`MongoAutoField`.

```python
DEFAULT_AUTO_FIELD = "django_mongodb.fields.MongoAutoField"
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
    default_auto_field = "django_mongodb.fields.MongoAutoField"


class MongoAuthConfig(AuthConfig):
    default_auto_field = "django_mongodb.fields.MongoAutoField"


class MongoContentTypesConfig(ContentTypesConfig):
    default_auto_field = "django_mongodb.fields.MongoAutoField"
```

Then replace each app reference in the `INSTALLED_APPS` setting with the new
``AppConfig``. For example, replace  `'django.contrib.admin'` with
`'mysite.apps.MongoAdminConfig'`.

Because all models must use `MongoAutoField`, each third-party and contrib app
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

## Known issues and limitations

- The following `QuerySet` methods aren't supported:
  - `aggregate()`
  - `dates()`
  - `datetimes()`
  - `distinct()`
  - `extra()`
  - `select_related()`

- Queries with joins aren't supported.

- `DateTimeField` doesn't support microsecond precision.

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

## Troubleshooting

TODO
