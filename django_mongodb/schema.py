from django.db.backends.base.schema import BaseDatabaseSchemaEditor

from .query import wrap_database_errors
from .utils import OperationCollector


class DatabaseSchemaEditor(BaseDatabaseSchemaEditor):
    def get_collection(self, name):
        if self.collect_sql:
            return OperationCollector(self.collected_sql, collection=self.connection.database[name])
        return self.connection.get_collection(name)

    def get_database(self):
        if self.collect_sql:
            return OperationCollector(self.collected_sql, db=self.connection.database)
        return self.connection.get_database()

    @wrap_database_errors
    def create_model(self, model):
        self.get_database().create_collection(model._meta.db_table)
        # Make implicit M2M tables.
        for field in model._meta.local_many_to_many:
            if field.remote_field.through._meta.auto_created:
                self.create_model(field.remote_field.through)

    def delete_model(self, model):
        # Delete implicit M2m tables.
        for field in model._meta.local_many_to_many:
            if field.remote_field.through._meta.auto_created:
                self.delete_model(field.remote_field.through)
        self.get_collection(model._meta.db_table).drop()

    def add_field(self, model, field):
        # Create implicit M2M tables.
        if field.many_to_many and field.remote_field.through._meta.auto_created:
            self.create_model(field.remote_field.through)
            return
        # Set default value on existing documents.
        if column := field.column:
            self.get_collection(model._meta.db_table).update_many(
                {}, [{"$set": {column: self.effective_default(field)}}]
            )

    def _alter_field(
        self,
        model,
        old_field,
        new_field,
        old_type,
        new_type,
        old_db_params,
        new_db_params,
        strict=False,
    ):
        collection = self.get_collection(model._meta.db_table)
        # Have they renamed the column?
        if old_field.column != new_field.column:
            collection.update_many({}, {"$rename": {old_field.column: new_field.column}})
        # Replace NULL with the field default if the field and was changed from
        # NULL to NOT NULL.
        if new_field.has_default() and old_field.null and not new_field.null:
            column = new_field.column
            default = self.effective_default(new_field)
            collection.update_many({column: {"$eq": None}}, [{"$set": {column: default}}])

    def remove_field(self, model, field):
        # Remove implicit M2M tables.
        if field.many_to_many and field.remote_field.through._meta.auto_created:
            self.delete_model(field.remote_field.through)
            return
        # Unset field on existing documents.
        if column := field.column:
            self.get_collection(model._meta.db_table).update_many({}, {"$unset": {column: ""}})

    def alter_index_together(self, model, old_index_together, new_index_together):
        pass

    def alter_unique_together(self, model, old_unique_together, new_unique_together):
        pass

    def add_index(self, model, index):
        pass

    def rename_index(self, model, old_index, new_index):
        pass

    def remove_index(self, model, index):
        pass

    def add_constraint(self, model, constraint):
        pass

    def remove_constraint(self, model, constraint):
        pass

    def alter_db_table(self, model, old_db_table, new_db_table):
        if old_db_table == new_db_table:
            return
        self.get_collection(old_db_table).rename(new_db_table)
