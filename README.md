# Django MongoDB Backend

This backend is currently in development and is not advised for Production workflows. Backwards incompatible
changes may be made without notice. We welcome your feedback as we continue to
explore and build. The best way to share this is via our [MongoDB Community Forum](https://www.mongodb.com/community/forums/tag/python)

## Install and usage

The development version of this package supports Django 5.0.x. To install it:

`pip install django-mongodb-backend`

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
