import copy
import time

import django
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.backends.utils import logger
from django.utils.version import get_version_tuple


def check_django_compatability():
    """
    Verify that this version of django-mongodb is compatible with the
    installed version of Django. For example, any django-mongodb 5.0.x is
    compatible with Django 5.0.y.
    """
    from . import __version__

    if django.VERSION[:2] != get_version_tuple(__version__)[:2]:
        A = django.VERSION[0]
        B = django.VERSION[1]
        raise ImproperlyConfigured(
            f"You must use the latest version of django-mongodb {A}.{B}.x "
            f"with Django {A}.{B}.y (found django-mongodb {__version__})."
        )


class CollectionDebugWrapper:
    def __init__(self, collection, db):
        self.collection = collection
        self.db = db

    def __getattr__(self, attr):
        return getattr(self.collection, attr)

    def profile_call(self, func, args=(), kwargs=None):
        start = time.monotonic()
        retval = func(*args, **kwargs or {})
        duration = time.monotonic() - start
        return duration, retval

    def log(self, op, duration, args, kwargs=None):
        # If kwargs are used by any operations in the future, they must be
        # added to this logging.
        msg = "(%.3f) %s"
        args = ", ".join(str(arg) for arg in args)
        operation = f"{self.collection.name}.{op}({args})"
        if len(settings.DATABASES) > 1:
            msg += f"; alias={self.db.alias}"
        self.db.queries_log.append(
            {
                "sql": operation,
                "time": "%.3f" % duration,
            }
        )
        logger.debug(
            msg,
            duration,
            operation,
            extra={
                "duration": duration,
                "sql": operation,
                "alias": self.db.alias,
            },
        )

    def logging_wrapper(method):
        def wrapper(self, *args, **kwargs):
            func = getattr(self.collection, method)
            # Collection.insert_many() mutates args (the documents) by adding
            #  _id. deepcopy() to avoid logging that version.
            original_args = copy.deepcopy(args)
            duration, retval = self.profile_call(func, args, kwargs)
            self.log(method, duration, original_args, kwargs)
            return retval

        return wrapper

    # These are the operations that this backend uses.
    aggregate = logging_wrapper("aggregate")
    insert_many = logging_wrapper("insert_many")
    delete_many = logging_wrapper("delete_many")
    update_many = logging_wrapper("update_many")

    del logging_wrapper
