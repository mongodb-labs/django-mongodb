from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.models import Index
from pymongo import ASCENDING, DESCENDING
from pymongo.operations import IndexModel

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
        self._create_model_indexes(model)
        # Make implicit M2M tables.
        for field in model._meta.local_many_to_many:
            if field.remote_field.through._meta.auto_created:
                self.create_model(field.remote_field.through)

    def _create_model_indexes(self, model):
        """
        Create all indexes (field indexes, index_together, Meta.indexes) for
        the specified model.
        """
        if not model._meta.managed or model._meta.proxy or model._meta.swapped:
            return
        # Field indexes
        for field in model._meta.local_fields:
            if self._field_should_be_indexed(model, field):
                self._add_field_index(model, field)
        # Meta.index_together (RemovedInDjango51Warning)
        for field_names in model._meta.index_together:
            self._add_composed_index(model, field_names)
        # Meta.indexes
        for index in model._meta.indexes:
            self.add_index(model, index)

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
        # Add an index, if required.
        if self._field_should_be_indexed(model, field):
            self._add_field_index(model, field)

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
            if self._field_should_be_indexed(model, field):
                self._remove_field_index(model, field)

    def alter_index_together(self, model, old_index_together, new_index_together):
        pass

    def alter_unique_together(self, model, old_unique_together, new_unique_together):
        pass

    def add_index(self, model, index, field=None):
        if index.contains_expressions:
            return
        index_orders = (
            [(field.column, ASCENDING)]
            if field
            else [
                # order is "" if ASCENDING or "DESC" if DESCENDING (see
                # django.db.models.indexes.Index.fields_orders).
                (model._meta.get_field(field_name).column, ASCENDING if order == "" else DESCENDING)
                for field_name, order in index.fields_orders
            ]
        )
        idx = IndexModel(index_orders, name=index.name)
        self.get_collection(model._meta.db_table).create_indexes([idx])

    def _add_composed_index(self, model, field_names):
        """Add an index on the given list of field_names."""
        idx = Index(fields=field_names)
        idx.set_name_with_model(model)
        self.add_index(model, idx)

    def _add_field_index(self, model, field):
        """Add an index on a field with db_index=True."""
        index = Index(fields=[field.name])
        index.name = self._create_index_name(model._meta.db_table, [field.column])
        self.add_index(model, index, field=field)

    def remove_index(self, model, index):
        if index.contains_expressions:
            return
        self.get_collection(model._meta.db_table).drop_index(index.name)

    def _remove_field_index(self, model, field):
        """Remove a field's db_index=True index."""
        collection = self.get_collection(model._meta.db_table)
        meta_index_names = {index.name for index in model._meta.indexes}
        index_names = self._constraint_names(
            model,
            [field.column],
            index=True,
            # Retrieve only BTREE indexes since this is what's created with
            # db_index=True.
            type_=Index.suffix,
            exclude=meta_index_names,
        )
        if len(index_names) != 1:
            num_found = len(index_names)
            raise ValueError(
                f"Found wrong number ({num_found}) of constraints for "
                f"{model._meta.db_table}.{field.column}."
            )
        collection.drop_index(index_names[0])

    def add_constraint(self, model, constraint):
        pass

    def remove_constraint(self, model, constraint):
        pass

    def alter_db_table(self, model, old_db_table, new_db_table):
        if old_db_table == new_db_table:
            return
        self.get_collection(old_db_table).rename(new_db_table)
