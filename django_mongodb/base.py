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
from .schema import DatabaseSchemaEditor


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
        return Collection(self.database, name, **kwargs)

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
            tz_aware=True,
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
