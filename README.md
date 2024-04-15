# MongoDB backend for Django

This library is in the early stages of development, and so it's possible the API may change in the future - we definitely want to continue expanding it. We welcome your feedback as we continue to explore and build this tool.

## Install and usage

Use the version of `django-mongodb` that corresponds to your version of
Django. For example, to get the latest compatible release for Django 5.0.x:

`pip install django-mongodb==0.1.*`

The minor release number of Django doesn't correspond to the minor release
number of django-mongodb. Use the latest minor release of each.

Configure the Django `DATABASES` setting similar to this:

```python
DATABASES = {
    "default": {
        "ENGINE": "django_mongodb",
        "NAME": "MY_DATABASE",
        "SCHEMA": "MY_SCHEMA",
        "WAREHOUSE": "MY_WAREHOUSE",
        "USER": "my_user",
        "PASSWORD": "my_password",
        "ACCOUNT": "my_account",
    },
}
```

## Known issues and limitations

TODO

## Troubleshooting

### Debug logging

TODO
