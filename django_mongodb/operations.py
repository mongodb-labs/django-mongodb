import datetime
import decimal
import uuid

from django.db.backends.base.operations import BaseDatabaseOperations


class DatabaseOperations(BaseDatabaseOperations):
    compiler_module = "django_mongodb.compiler"

    def get_db_converters(self, expression):
        converters = super().get_db_converters(expression)
        internal_type = expression.output_field.get_internal_type()
        if internal_type == "DateField":
            converters.append(self.convert_datefield_value)
        elif internal_type == "DateTimeField":
            converters.append(self.convert_datetimefield_value)
        elif internal_type == "DecimalField":
            converters.append(self.convert_decimalfield_value)
        elif internal_type == "TimeField":
            converters.append(self.convert_timefield_value)
        elif internal_type == "UUIDField":
            converters.append(self.convert_uuidfield_value)
        return converters

    def convert_datefield_value(self, value, expression, connection):
        if value is not None:
            value = datetime.date.fromisoformat(value)
        return value

    def convert_datetimefield_value(self, value, expression, connection):
        if value is not None:
            value = datetime.datetime.fromisoformat(value)
        return value

    def convert_decimalfield_value(self, value, expression, connection):
        if value is not None:
            value = decimal.Decimal(value)
        return value

    def convert_timefield_value(self, value, expression, connection):
        if value is not None:
            value = datetime.time.fromisoformat(value)
        return value

    def convert_uuidfield_value(self, value, expression, connection):
        if value is not None:
            value = uuid.UUID(value)
        return value

    def prep_for_like_query(self, x):
        # Override value escaping for LIKE queries.
        return str(x)

    def quote_name(self, name):
        if name.startswith('"') and name.endswith('"'):
            return name  # Quoting once is enough.
        return name

    def sql_flush(self, style, tables, *, reset_sequences=False, allow_cascade=False):
        """
        Return a list of the tables which will be passed as argument to
        execute_sql_flush().
        """
        return tables

    def execute_sql_flush(self, tables):
        for table in tables:
            if table.startswith("system."):
                # Do not drop system collections.
                continue

            collection = self.connection.database[table]
            options = collection.options()
            if not options.get("capped", False):
                collection.drop()

    def prep_lookup_value(self, value, field, lookup):
        """
        Perform type-conversion on `value` before using as a filter parameter.

        This precomputes `field`'s kind and a db_type for the field (or the
        primary key of the related model for ForeignKeys etc.) and knows that
        arguments to the `isnull` lookup (`True` or `False`) should not be
        converted, while some other lookups take a list of arguments.
        """
        field, field_kind, db_type = self._convert_as(field, lookup)

        # Argument to the "isnull" lookup is just a boolean, while some
        # other lookups take a list of values.
        if lookup == "isnull":
            return value
        if lookup in ("in", "range", "year"):
            return [
                self._prep_lookup_value(subvalue, field, field_kind, db_type, lookup)
                for subvalue in value
            ]
        return self._prep_lookup_value(value, field, field_kind, db_type, lookup)

    def _prep_lookup_value(self, value, field, field_kind, db_type, lookup):
        if value is None:
            return None

        if field_kind == "DecimalField":
            value = self.adapt_decimalfield_value(value, field.max_digits, field.decimal_places)
        return value

    def _convert_as(self, field, lookup):
        """
        Compute parameters that should be used for preparing the field
        for the database or deconverting a database value for it.
        """
        db_type = field.db_type(self.connection)

        if getattr(field, "rel", None) is not None:
            field = field.rel.get_related_field()
        field_kind = field.get_internal_type()

        # Values for standard month / day queries are integers.
        if field_kind in ("DateField", "DateTimeField") and lookup in ("month", "day"):
            db_type = "integer"

        return field, field_kind, db_type
