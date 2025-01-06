import copy
import time

import django
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.backends.utils import logger
from django.utils.version import get_version_tuple
from pymongo.uri_parser import parse_uri as pymongo_parse_uri


def check_django_compatability():
    """
    Verify that this version of django-mongodb-backend is compatible with the
    installed version of Django. For example, any django-mongodb-backend 5.0.x is
    compatible with Django 5.0.y.
    """
    from . import __version__

    if django.VERSION[:2] != get_version_tuple(__version__)[:2]:
        A = django.VERSION[0]
        B = django.VERSION[1]
        raise ImproperlyConfigured(
            f"You must use the latest version of django-mongodb-backend {A}.{B}.x "
            f"with Django {A}.{B}.y (found django-mongodb-backend {__version__})."
        )


def parse_uri(uri, conn_max_age=0, test=None):
    """
    Convert the given uri into a dictionary suitable for Django's DATABASES
    setting.
    """
    uri = pymongo_parse_uri(uri)
    host = None
    port = None
    if uri["fqdn"]:
        # This is a SRV URI and the host is the fqdn.
        host = f"mongodb+srv://{uri['fqdn']}"
    else:
        nodelist = uri.get("nodelist")
        if len(nodelist) == 1:
            host, port = nodelist[0]
        elif len(nodelist) > 1:
            host = ",".join([f"{host}:{port}" for host, port in nodelist])
    settings_dict = {
        "ENGINE": "django_mongodb_backend",
        "NAME": uri["database"],
        "HOST": host,
        "PORT": port,
        "USER": uri.get("username"),
        "PASSWORD": uri.get("password"),
        "OPTIONS": uri.get("options"),
        "CONN_MAX_AGE": conn_max_age,
    }
    if test:
        settings_dict["TEST"] = test
    return settings_dict


def set_wrapped_methods(cls):
    """Initialize the wrapped methods on cls."""
    if hasattr(cls, "logging_wrapper"):
        for attr in cls.wrapped_methods:
            setattr(cls, attr, cls.logging_wrapper(attr))
        del cls.logging_wrapper
    return cls


@set_wrapped_methods
class OperationDebugWrapper:
    # The PyMongo database and collection methods that this backend uses.
    wrapped_methods = {
        "aggregate",
        "create_collection",
        "create_indexes",
        "drop",
        "index_information",
        "insert_many",
        "delete_many",
        "drop_index",
        "rename",
        "update_many",
    }

    def __init__(self, db, collection=None):
        self.collection = collection
        self.db = db
        use_collection = collection is not None
        self.collection_name = f"{collection.name}." if use_collection else ""
        self.wrapped = self.collection if use_collection else self.db.database

    def __getattr__(self, attr):
        return getattr(self.wrapped, attr)

    def profile_call(self, func, args=(), kwargs=None):
        start = time.monotonic()
        retval = func(*args, **kwargs or {})
        duration = time.monotonic() - start
        return duration, retval

    def log(self, op, duration, args, kwargs=None):
        # If kwargs are used by any operations in the future, they must be
        # added to this logging.
        msg = "(%.3f) %s"
        args = ", ".join(repr(arg) for arg in args)
        operation = f"db.{self.collection_name}{op}({args})"
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
            func = getattr(self.wrapped, method)
            # Collection.insert_many() mutates args (the documents) by adding
            #  _id. deepcopy() to avoid logging that version.
            original_args = copy.deepcopy(args)
            duration, retval = self.profile_call(func, args, kwargs)
            self.log(method, duration, original_args, kwargs)
            return retval

        return wrapper


@set_wrapped_methods
class OperationCollector(OperationDebugWrapper):
    def __init__(self, collected_sql=None, *, collection=None, db=None):
        super().__init__(db, collection)
        self.collected_sql = collected_sql

    def log(self, op, args, kwargs=None):
        args = ", ".join(repr(arg) for arg in args)
        operation = f"db.{self.collection_name}{op}({args})"
        self.collected_sql.append(operation)

    def logging_wrapper(method):
        def wrapper(self, *args, **kwargs):
            self.log(method, args, kwargs)

        return wrapper
