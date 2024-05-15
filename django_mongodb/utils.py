import copy
import time

import django
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.backends.utils import logger
from django.utils.version import get_version_tuple
from pymongo.cursor import Cursor


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
        msg = "(%.3f) %s"
        args = " ".join(str(arg) for arg in args)
        operation = f"{self.collection.name}.{op}({args})"
        kwargs = {k: v for k, v in kwargs.items() if v}
        if kwargs:
            operation += f"; kwargs={kwargs}"
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
                "kwargs": kwargs,
                "alias": self.db.alias,
            },
        )

    def find(self, *args, **kwargs):
        return DebugCursor(self, self.collection, *args, **kwargs)

    def logging_wrapper(method):
        def wrapper(self, *args, **kwargs):
            func = getattr(self.collection, method)
            # Collection.insert_one() mutates args[0] (the document) by adding
            # the _id. deepcopy() to avoid logging that version.
            original_args = copy.deepcopy(args)
            duration, retval = self.profile_call(func, args, kwargs)
            self.log(method, duration, original_args, kwargs)
            return retval

        return wrapper

    # These are the operations that this backend uses.
    count_documents = logging_wrapper("count_documents")
    insert_many = logging_wrapper("insert_many")
    delete_many = logging_wrapper("delete_many")
    update_many = logging_wrapper("update_many")

    del logging_wrapper


class DebugCursor(Cursor):
    def __init__(self, collection_wrapper, *args, **kwargs):
        self.collection_wrapper = collection_wrapper
        super().__init__(*args, **kwargs)

    def _refresh(self):
        super_method = super()._refresh
        if self._Cursor__id is not None:
            return super_method()
        # self.__id is None: first time the .find() iterator is
        # entered. find() profiling happens here.
        duration, retval = self.collection_wrapper.profile_call(super_method)
        kwargs = {
            "limit": self._Cursor__limit,
            "skip": self._Cursor__skip,
            "sort": self._Cursor__ordering,
        }
        self.collection_wrapper.log("find", duration, [self._Cursor__spec], kwargs)
        return retval
