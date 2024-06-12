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
    - `ExtractQuarter`
    - `Now`
    - `Sign`
    - `TruncDate`
    - `TruncTime`

- The `tzinfo` parameter of the `Trunc` database functions doesn't work
  properly because MongoDB converts the result back to UTC.

## Troubleshooting

TODO
