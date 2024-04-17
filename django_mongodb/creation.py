from django.db.backends.base.creation import BaseDatabaseCreation


class DatabaseCreation(BaseDatabaseCreation):
    def _execute_create_test_db(self, cursor, parameters, keepdb=False):
        if not keepdb:
            self._destroy_test_db(parameters["dbname"], verbosity=0)

    def _destroy_test_db(self, test_database_name, verbosity):
        for collection in self.connection.introspection.table_names():
            if not collection.startswith("system."):
                self.connection.database.drop_collection(collection)
