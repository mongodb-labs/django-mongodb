import itertools

from django.db import connection
from django.test import TransactionTestCase

from .models import Address, Author, Book, new_apps


class SchemaTests(TransactionTestCase):
    available_apps = []
    models = [Address, Author, Book]

    # Utility functions

    def setUp(self):
        # local_models should contain test dependent model classes that will be
        # automatically removed from the app cache on test tear down.
        self.local_models = []
        # isolated_local_models contains models that are in test methods
        # decorated with @isolate_apps.
        self.isolated_local_models = []

    def tearDown(self):
        # Delete any tables made for our models
        self.delete_tables()
        new_apps.clear_cache()
        for model in new_apps.get_models():
            model._meta._expire_cache()
        if "schema" in new_apps.all_models:
            for model in self.local_models:
                for many_to_many in model._meta.many_to_many:
                    through = many_to_many.remote_field.through
                    if through and through._meta.auto_created:
                        del new_apps.all_models["schema"][through._meta.model_name]
                del new_apps.all_models["schema"][model._meta.model_name]
        if self.isolated_local_models:
            with connection.schema_editor() as editor:
                for model in self.isolated_local_models:
                    editor.delete_model(model)

    def delete_tables(self):
        "Deletes all model tables for our models for a clean test environment"
        converter = connection.introspection.identifier_converter
        with connection.schema_editor() as editor:
            connection.disable_constraint_checking()
            table_names = connection.introspection.table_names()
            if connection.features.ignores_table_name_case:
                table_names = [table_name.lower() for table_name in table_names]
            for model in itertools.chain(SchemaTests.models, self.local_models):
                tbl = converter(model._meta.db_table)
                if connection.features.ignores_table_name_case:
                    tbl = tbl.lower()
                if tbl in table_names:
                    editor.delete_model(model)
                    table_names.remove(tbl)
            connection.enable_constraint_checking()

    def get_indexes(self, table):
        """
        Get the indexes on the table using a new cursor.
        """
        with connection.cursor() as cursor:
            return [
                c["columns"][0]
                for c in connection.introspection.get_constraints(cursor, table).values()
                if c["index"] and len(c["columns"]) == 1
            ]

    def get_uniques(self, table):
        with connection.cursor() as cursor:
            return [
                c["columns"][0]
                for c in connection.introspection.get_constraints(cursor, table).values()
                if c["unique"] and len(c["columns"]) == 1
            ]

    def get_constraints(self, table):
        """
        Get the constraints on a table using a new cursor.
        """
        with connection.cursor() as cursor:
            return connection.introspection.get_constraints(cursor, table)

    def get_constraints_for_columns(self, model, columns):
        constraints = self.get_constraints(model._meta.db_table)
        constraints_for_column = []
        for name, details in constraints.items():
            if details["columns"] == columns:
                constraints_for_column.append(name)
        return sorted(constraints_for_column)

    def check_added_field_default(
        self,
        schema_editor,
        model,
        field,
        field_name,
        expected_default,
        cast_function=None,
    ):
        schema_editor.add_field(model, field)
        database_default = connection.database[model._meta.db_table].find_one().get(field_name)
        if cast_function and type(database_default) is not type(expected_default):
            database_default = cast_function(database_default)
        self.assertEqual(database_default, expected_default)

    def get_constraints_count(self, table, column, fk_to):
        """
        Return a dict with keys 'fks', 'uniques, and 'indexes' indicating the
        number of foreign keys, unique constraints, and indexes on
        `table`.`column`. The `fk_to` argument is a 2-tuple specifying the
        expected foreign key relationship's (table, column).
        """
        with connection.cursor() as cursor:
            constraints = connection.introspection.get_constraints(cursor, table)
        counts = {"fks": 0, "uniques": 0, "indexes": 0}
        for c in constraints.values():
            if c["columns"] == [column]:
                if c["foreign_key"] == fk_to:
                    counts["fks"] += 1
                if c["unique"]:
                    counts["uniques"] += 1
                elif c["index"]:
                    counts["indexes"] += 1
        return counts

    def assertIndexOrder(self, table, index, order):
        constraints = self.get_constraints(table)
        self.assertIn(index, constraints)
        index_orders = constraints[index]["orders"]
        self.assertTrue(
            all(val == expected for val, expected in zip(index_orders, order, strict=True))
        )

    def assertForeignKeyExists(self, model, column, expected_fk_table, field="id"):
        """
        Fail if the FK constraint on `model.Meta.db_table`.`column` to
        `expected_fk_table`.id doesn't exist.
        """
        if not connection.features.can_introspect_foreign_keys:
            return
        constraints = self.get_constraints(model._meta.db_table)
        constraint_fk = None
        for details in constraints.values():
            if details["columns"] == [column] and details["foreign_key"]:
                constraint_fk = details["foreign_key"]
                break
        self.assertEqual(constraint_fk, (expected_fk_table, field))

    def assertForeignKeyNotExists(self, model, column, expected_fk_table):
        if not connection.features.can_introspect_foreign_keys:
            return
        with self.assertRaises(AssertionError):
            self.assertForeignKeyExists(model, column, expected_fk_table)

    def assertTableExists(self, model):
        self.assertIn(model._meta.db_table, connection.introspection.table_names())

    def assertTableNotExists(self, model):
        self.assertNotIn(model._meta.db_table, connection.introspection.table_names())

    # Tests
    def test_db_index(self):
        """Field(db_index=True) on an embedded model."""
        with connection.schema_editor() as editor:
            # Create the table
            editor.create_model(Book)
            # The table is there
            self.assertTableExists(Book)
            # Embedded indexes are created.
            self.assertEqual(
                self.get_constraints_for_columns(Book, ["author.age"]),
                ["schema__book_author.age_dc08100b"],
            )
            self.assertEqual(
                self.get_constraints_for_columns(Book, ["author.address.zip_code"]),
                ["schema__book_author.address.zip_code_7b9a9307"],
            )
            # Clean up that table
            editor.delete_model(Book)
        # The table is gone
        self.assertTableNotExists(Author)

    def test_unique(self):
        """Field(unique=True) on an embedded model."""
        with connection.schema_editor() as editor:
            editor.create_model(Book)
            self.assertTableExists(Book)
            # Embedded uniques are created.
            self.assertEqual(
                self.get_constraints_for_columns(Book, ["author.employee_id"]),
                ["schema__book_author.employee_id_7d4d3eff_uniq"],
            )
            self.assertEqual(
                self.get_constraints_for_columns(Book, ["author.address.uid"]),
                ["schema__book_author.address.uid_8124a01f_uniq"],
            )
            # Clean up that table
            editor.delete_model(Book)
        self.assertTableNotExists(Author)

    def test_unique_together(self):
        """Meta.unique_together on an embedded model."""
        with connection.schema_editor() as editor:
            editor.create_model(Book)
            self.assertTableExists(Book)
            # Embedded uniques are created.
            self.assertEqual(
                self.get_constraints_for_columns(
                    Book, ["author.unique_together_three", "author.unique_together_four"]
                ),
                [
                    "schema__author_author.unique_together_three_author.unique_together_four_39e1cb43_uniq"
                ],
            )
            self.assertEqual(
                self.get_constraints_for_columns(
                    Book,
                    ["author.address.unique_together_one", "author.address.unique_together_two"],
                ),
                [
                    "schema__address_author.address.unique_together_one_author.address.unique_together_two_de682e30_uniq"
                ],
            )
            editor.delete_model(Author)
        self.assertTableNotExists(Author)
