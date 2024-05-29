import re

from django.core.exceptions import ImproperlyConfigured
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.signals import connection_created
from pymongo.collection import Collection
from pymongo.mongo_client import MongoClient

from . import dbapi as Database
from .client import DatabaseClient
from .creation import DatabaseCreation
from .features import DatabaseFeatures
from .introspection import DatabaseIntrospection
from .operations import DatabaseOperations
from .query_utils import safe_regex
from .schema import DatabaseSchemaEditor
from .utils import CollectionDebugWrapper


class Cursor:
    """A "nodb" cursor that does nothing except work on a context manager."""

    def __enter__(self):
        pass

    def __exit__(self, exception_type, exception_value, exception_traceback):
        pass


class DatabaseWrapper(BaseDatabaseWrapper):
    data_types = {
        "AutoField": "int",
        "BigAutoField": "long",
        "BinaryField": "binData",
        "BooleanField": "bool",
        "CharField": "string",
        "DateField": "date",
        "DateTimeField": "date",
        "DecimalField": "decimal",
        "DurationField": "long",
        "FileField": "string",
        "FilePathField": "string",
        "FloatField": "double",
        "IntegerField": "int",
        "BigIntegerField": "long",
        "GenericIPAddressField": "string",
        "NullBooleanField": "bool",
        "OneToOneField": "int",
        "PositiveIntegerField": "long",
        "PositiveSmallIntegerField": "int",
        "SlugField": "string",
        "SmallIntegerField": "int",
        "TextField": "string",
        "TimeField": "date",
        "UUIDField": "string",
    }
    # Django uses these operators to generate SQL queries before it generates
    # MQL queries.
    operators = {
        "exact": "= %s",
        "iexact": "= UPPER(%s)",
        "contains": "LIKE %s",
        "icontains": "LIKE UPPER(%s)",
        "regex": "~ %s",
        "iregex": "~* %s",
        "gt": "> %s",
        "gte": ">= %s",
        "lt": "< %s",
        "lte": "<= %s",
        "startswith": "LIKE %s",
        "endswith": "LIKE %s",
        "istartswith": "LIKE UPPER(%s)",
        "iendswith": "LIKE UPPER(%s)",
    }
    mongo_operators = {
        "exact": lambda val: val,
        "gt": lambda val: {"$gt": val},
        "gte": lambda val: {"$gte": val},
        "lt": lambda val: {"$lt": val},
        "lte": lambda val: {"$lte": val},
        "in": lambda val: {"$in": val},
        "range": lambda val: {"$gte": val[0], "$lte": val[1]},
        "isnull": lambda val: None if val else {"$ne": None},
        "iexact": safe_regex("^%s$", re.IGNORECASE),
        "startswith": safe_regex("^%s"),
        "istartswith": safe_regex("^%s", re.IGNORECASE),
        "endswith": safe_regex("%s$"),
        "iendswith": safe_regex("%s$", re.IGNORECASE),
        "contains": safe_regex("%s"),
        "icontains": safe_regex("%s", re.IGNORECASE),
        "regex": lambda val: re.compile(val),
        "iregex": lambda val: re.compile(val, re.IGNORECASE),
    }
    mongo_aggregations = {
        "exact": lambda a, b: {"$eq": [a, b]},
        "gt": lambda a, b: {"$gt": [a, b]},
        "gte": lambda a, b: {"$gte": [a, b]},
        "lt": lambda a, b: {"$lt": [a, b]},
        "lte": lambda a, b: {"$lte": [a, b]},
    }

    display_name = "MongoDB"
    vendor = "mongodb"
    Database = Database
    SchemaEditorClass = DatabaseSchemaEditor
    client_class = DatabaseClient
    creation_class = DatabaseCreation
    features_class = DatabaseFeatures
    introspection_class = DatabaseIntrospection
    ops_class = DatabaseOperations

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connected = False
        del self.connection

    def get_collection(self, name, **kwargs):
        collection = Collection(self.database, name, **kwargs)
        if self.queries_logged:
            collection = CollectionDebugWrapper(collection, self)
        return collection

    def __getattr__(self, attr):
        """
        Connect to the database the first time `connection` or `database` are
        accessed.
        """
        if attr in ["connection", "database"]:
            assert not self.connected
            self._connect()
            return getattr(self, attr)
        raise AttributeError(attr)

    def _connect(self):
        settings_dict = self.settings_dict

        options = settings_dict["OPTIONS"]
        # TODO: review and document OPERATIONS: https://github.com/mongodb-labs/django-mongodb/issues/6
        self.operation_flags = options.pop("OPERATIONS", {})
        if not any(k in ["save", "delete", "update"] for k in self.operation_flags):
            # Flags apply to all operations.
            flags = self.operation_flags
            self.operation_flags = {"save": flags, "delete": flags, "update": flags}

        self.connection = MongoClient(
            host=settings_dict["HOST"] or None,
            port=int(settings_dict["PORT"] or 27017),
            **options,
        )
        db_name = settings_dict["NAME"]
        if db_name:
            self.database = self.connection[db_name]

        user = settings_dict["USER"]
        password = settings_dict["PASSWORD"]
        if user and password and not self.database.authenticate(user, password):
            raise ImproperlyConfigured("Invalid username or password.")

        self.connected = True
        connection_created.send(sender=self.__class__, connection=self)

    def _commit(self):
        pass

    def _rollback(self):
        pass

    def close(self):
        if self.connected:
            del self.connection
            del self.database
            self.connected = False

    def cursor(self):
        return Cursor()
