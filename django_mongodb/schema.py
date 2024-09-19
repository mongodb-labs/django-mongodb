from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.models import Index, UniqueConstraint
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
        Create all indexes (field indexes & uniques, Meta.index_together,
        Meta.unique_together, Meta.constraints, Meta.indexes) for the model.
        """
        if not model._meta.managed or model._meta.proxy or model._meta.swapped:
            return
        # Field indexes and uniques
        for field in model._meta.local_fields:
            if self._field_should_be_indexed(model, field):
                self._add_field_index(model, field)
            elif self._field_should_have_unique(field):
                self._add_field_unique(model, field)
        # Meta.index_together (RemovedInDjango51Warning)
        for field_names in model._meta.index_together:
            self._add_composed_index(model, field_names)
        # Meta.unique_together
        if model._meta.unique_together:
            self.alter_unique_together(model, [], model._meta.unique_together)
        # Meta.constraints
        for constraint in model._meta.constraints:
            self.add_constraint(model, constraint)
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
        # Add an index or unique, if required.
        if self._field_should_be_indexed(model, field):
            self._add_field_index(model, field)
        elif self._field_should_have_unique(field):
            self._add_field_unique(model, field)

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
        # Has unique been removed?
        old_field_unique = self._field_should_have_unique(old_field)
        new_field_unique = self._field_should_have_unique(new_field)
        if old_field_unique and not new_field_unique:
            self._remove_field_unique(model, old_field)
        # Removed an index?
        old_field_indexed = self._field_should_be_indexed(model, old_field)
        new_field_indexed = self._field_should_be_indexed(model, new_field)
        if old_field_indexed and not new_field_indexed:
            self._remove_field_index(model, old_field)
        # Have they renamed the column?
        if old_field.column != new_field.column:
            collection.update_many({}, {"$rename": {old_field.column: new_field.column}})
            # Move index to the new field, if needed.
            if old_field_indexed and new_field_indexed:
                self._remove_field_index(model, old_field)
                self._add_field_index(model, new_field)
            # Move unique to the new field, if needed.
            if old_field_unique and new_field_unique:
                self._remove_field_unique(model, old_field)
                self._add_field_unique(model, new_field)
        # Replace NULL with the field default if the field and was changed from
        # NULL to NOT NULL.
        if new_field.has_default() and old_field.null and not new_field.null:
            column = new_field.column
            default = self.effective_default(new_field)
            collection.update_many({column: {"$eq": None}}, [{"$set": {column: default}}])
        # Added an index?
        if not old_field_indexed and new_field_indexed:
            self._add_field_index(model, new_field)
        # Added a unique?
        if not old_field_unique and new_field_unique:
            self._add_field_unique(model, new_field)

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
            elif self._field_should_have_unique(field):
                self._remove_field_unique(model, field)

    def alter_index_together(self, model, old_index_together, new_index_together):
        olds = {tuple(fields) for fields in old_index_together}
        news = {tuple(fields) for fields in new_index_together}
        # Deleted indexes
        for field_names in olds.difference(news):
            self._remove_composed_index(model, field_names, {"index": True, "unique": False})
        # Created indexes
        for field_names in news.difference(olds):
            self._add_composed_index(model, field_names)

    def alter_unique_together(self, model, old_unique_together, new_unique_together):
        olds = {tuple(fields) for fields in old_unique_together}
        news = {tuple(fields) for fields in new_unique_together}
        # Deleted uniques
        for field_names in olds.difference(news):
            self._remove_composed_index(
                model,
                field_names,
                {"unique": True, "primary_key": False},
            )
        # Created uniques
        for field_names in news.difference(olds):
            columns = [model._meta.get_field(field).column for field in field_names]
            name = str(self._unique_constraint_name(model._meta.db_table, columns))
            constraint = UniqueConstraint(fields=field_names, name=name)
            self.add_constraint(model, constraint)

    def add_index(self, model, index, field=None, unique=False):
        if index.contains_expressions:
            return
        kwargs = {}
        if unique:
            filter_expression = {}
            # Indexing on $type matches the value of most SQL databases by
            # allowing multiple null values for the unique constraint.
            if field:
                filter_expression[field.column] = {"$type": field.db_type(self.connection)}
            else:
                for field_name, _ in index.fields_orders:
                    field_ = model._meta.get_field(field_name)
                    filter_expression[field_.column] = {"$type": field_.db_type(self.connection)}
            kwargs = {"partialFilterExpression": filter_expression, "unique": True}
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
        idx = IndexModel(index_orders, name=index.name, **kwargs)
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

    def _remove_composed_index(self, model, field_names, constraint_kwargs):
        """
        Remove the index on the given list of field_names created by
        index/unique_together, depending on constraint_kwargs.
        """
        meta_constraint_names = {constraint.name for constraint in model._meta.constraints}
        meta_index_names = {constraint.name for constraint in model._meta.indexes}
        columns = [model._meta.get_field(field).column for field in field_names]
        constraint_names = self._constraint_names(
            model,
            columns,
            exclude=meta_constraint_names | meta_index_names,
            **constraint_kwargs,
        )
        if len(constraint_names) != 1:
            num_found = len(constraint_names)
            columns_str = ", ".join(columns)
            raise ValueError(
                f"Found wrong number ({num_found}) of constraints for "
                f"{model._meta.db_table}({columns_str})."
            )
        collection = self.get_collection(model._meta.db_table)
        collection.drop_index(constraint_names[0])

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

    def add_constraint(self, model, constraint, field=None):
        if isinstance(constraint, UniqueConstraint) and self._unique_supported(
            condition=constraint.condition,
            deferrable=constraint.deferrable,
            include=constraint.include,
            expressions=constraint.expressions,
            nulls_distinct=constraint.nulls_distinct,
        ):
            idx = Index(fields=constraint.fields, name=constraint.name)
            self.add_index(model, idx, field=field, unique=True)

    def _add_field_unique(self, model, field):
        name = str(self._unique_constraint_name(model._meta.db_table, [field.column]))
        constraint = UniqueConstraint(fields=[field.name], name=name)
        self.add_constraint(model, constraint, field=field)

    def remove_constraint(self, model, constraint):
        if isinstance(constraint, UniqueConstraint) and self._unique_supported(
            condition=constraint.condition,
            deferrable=constraint.deferrable,
            include=constraint.include,
            expressions=constraint.expressions,
            nulls_distinct=constraint.nulls_distinct,
        ):
            idx = Index(fields=constraint.fields, name=constraint.name)
            self.remove_index(model, idx)

    def _remove_field_unique(self, model, field):
        # Find the unique constraint for this field
        meta_constraint_names = {constraint.name for constraint in model._meta.constraints}
        constraint_names = self._constraint_names(
            model,
            [field.column],
            unique=True,
            primary_key=False,
            exclude=meta_constraint_names,
        )
        if len(constraint_names) != 1:
            num_found = len(constraint_names)
            raise ValueError(
                f"Found wrong number ({num_found}) of unique constraints for "
                f"{model._meta.db_table}.{field.column}."
            )
        self.get_collection(model._meta.db_table).drop_index(constraint_names[0])

    def alter_db_table(self, model, old_db_table, new_db_table):
        if old_db_table == new_db_table:
            return
        self.get_collection(old_db_table).rename(new_db_table)

    def _field_should_have_unique(self, field):
        db_type = field.db_type(self.connection)
        # The _id column is automatically unique.
        return db_type and field.unique and field.column != "_id"
