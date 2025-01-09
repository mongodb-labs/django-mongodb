# MongoDB backend for Django

This backend is currently in development and is not advised for Production workflows. Backwards incompatible
changes may be made without notice. We welcome your feedback as we continue to
explore and build. The best way to share this is via our [MongoDB Community Forum](https://www.mongodb.com/community/forums/tag/python)

## Install and usage

The development version of this package supports Django 5.0.x. To install it:

`pip install git+https://github.com/mongodb-labs/django-mongodb-backend`

### Specifying the default primary key field

In your Django settings, you must specify that all models should use
`ObjectIdAutoField`.

You can create a new project that's configured based on these steps using a
project template:

```bash
$ django-admin startproject mysite --template https://github.com/mongodb-labs/django-mongodb-project/archive/refs/heads/5.0.x.zip
```
(where "5.0" matches the version of Django that you're using.)

This template includes the following line in `settings.py`:

```python
DEFAULT_AUTO_FIELD = "django_mongodb_backend.fields.ObjectIdAutoField"
```

But this setting won't override any apps that have an `AppConfig` that
specifies `default_auto_field`. For those apps, you'll need to create a custom
`AppConfig`.

For example, the project template includes `<project_name>/apps.py`:

```python
from django.contrib.admin.apps import AdminConfig
from django.contrib.auth.apps import AuthConfig
from django.contrib.contenttypes.apps import ContentTypesConfig


class MongoAdminConfig(AdminConfig):
    default_auto_field = "django_mongodb_backend.fields.ObjectIdAutoField"


class MongoAuthConfig(AuthConfig):
    default_auto_field = "django_mongodb_backend.fields.ObjectIdAutoField"


class MongoContentTypesConfig(ContentTypesConfig):
    default_auto_field = "django_mongodb_backend.fields.ObjectIdAutoField"
```

Each app reference in the `INSTALLED_APPS` setting must point to the
corresponding ``AppConfig``. For example, instead of `'django.contrib.admin'`,
the template uses `'<project_name>.apps.MongoAdminConfig'`.

### Configuring migrations

Because all models must use `ObjectIdAutoField`, each third-party and contrib app
you use needs to have its own migrations specific to MongoDB.

For example, `settings.py` in the project template specifies:

```python
MIGRATION_MODULES = {
    "admin": "mongo_migrations.admin",
    "auth": "mongo_migrations.auth",
    "contenttypes": "mongo_migrations.contenttypes",
}
```

The project template includes these migrations, but you can generate them if
you're setting things up manually or if you need to create migrations for
third-party apps. For example:

```console
$ python manage.py makemigrations admin auth contenttypes
Migrations for 'admin':
  mongo_migrations/admin/0001_initial.py
    - Create model LogEntry
...
```

### Creating Django applications

Whenever you run `python manage.py startapp`, you must remove the line:

`default_auto_field = 'django.db.models.BigAutoField'`

from the new application's `apps.py` file (or change it to reference
 `"django_mongodb_backend.fields.ObjectIdAutoField"`).

Alternatively, you can use the following `startapp` template which includes
this change:

```bash
$ python manage.py startapp myapp --template https://github.com/mongodb-labs/django-mongodb-app/archive/refs/heads/5.0.x.zip
```
(where "5.0" matches the version of Django that you're using.)

### Configuring the `DATABASES` setting

After you've set up a project, configure Django's `DATABASES` setting similar
to this:

```python
DATABASES = {
    "default": {
        "ENGINE": "django_mongodb_backend",
        "HOST": "mongodb+srv://cluster0.example.mongodb.net",
        "NAME": "my_database",
        "USER": "my_user",
        "PASSWORD": "my_password",
        "PORT": 27017,
        "OPTIONS": {
            # Example:
            "retryWrites": "true",
            "w": "majority",
            "tls": "false",
        },
    },
}
```

For a localhost configuration, you can omit `HOST` or specify
`"HOST": "localhost"`.

`HOST` only needs a scheme prefix for SRV connections (`mongodb+srv://`). A
`mongodb://` prefix is never required.

`OPTIONS` is an optional dictionary of parameters that will be passed to
[`MongoClient`](https://pymongo.readthedocs.io/en/stable/api/pymongo/mongo_client.html).

`USER`, `PASSWORD`, and `PORT` (if 27017) may also be optional.

For a replica set or sharded cluster where you have multiple hosts, include
all of them in `HOST`, e.g.
`"mongodb://mongos0.example.com:27017,mongos1.example.com:27017"`.

Alternatively, if you prefer to simply paste in a MongoDB URI rather than parse
it into the format above, you can use:

```python
import django_mongodb_backend

MONGODB_URI = "mongodb+srv://my_user:my_password@cluster0.example.mongodb.net/myDatabase?retryWrites=true&w=majority&tls=false"
DATABASES["default"] = django_mongodb_backend.parse_uri(MONGODB_URI)
```

This constructs a `DATABASES` setting equivalent to the first example.

#### `django_mongodb_backend.parse_uri(uri, conn_max_age=0, test=None)`

`parse_uri()` provides a few options to customize the resulting `DATABASES`
setting, but for maximum flexibility, construct `DATABASES` manually as
described above.

- Use `conn_max_age` to configure [persistent database connections](
  https://docs.djangoproject.com/en/stable/ref/databases/#persistent-database-connections).
- Use `test` to provide a dictionary of [settings for test databases](
  https://docs.djangoproject.com/en/stable/ref/settings/#test).

Congratulations, your project is ready to go!

## Notes on Django QuerySets

* `QuerySet.explain()` supports the [`comment` and `verbosity` options](
  https://www.mongodb.com/docs/manual/reference/command/explain/#command-fields).

   Example: `QuerySet.explain(comment="...", verbosity="...")`

   Valid values for `verbosity` are `"queryPlanner"` (default),
   `"executionStats"`, and `"allPlansExecution"`.

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

- Due to the lack of ability to introspect MongoDB collection schema,
  `migrate --fake-initial` isn't supported.

## Troubleshooting

### Debug logging

To troubleshoot MongoDB connectivity issues, you can enable [PyMongo's logging](
https://pymongo.readthedocs.io/en/stable/examples/logging.html) using
[Django's `LOGGING` setting](https://docs.djangoproject.com/en/stable/topics/logging/).

This is a minimal `LOGGING` setting that enables PyMongo's `DEBUG` logging:

```python
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "pymongo": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
    },
}
```
