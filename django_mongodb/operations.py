import datetime
import decimal
import uuid

from django.conf import settings
from django.db.backends.base.operations import BaseDatabaseOperations
from django.utils import timezone


class DatabaseOperations(BaseDatabaseOperations):
    compiler_module = "django_mongodb.compiler"

    def adapt_datefield_value(self, value):
        """Store DateField as datetime."""
        if value is None:
            return None
        return datetime.datetime.combine(value, datetime.datetime.min.time())

    def adapt_datetimefield_value(self, value):
        if not settings.USE_TZ and value is not None and timezone.is_naive(value):
            value = timezone.make_aware(value)
        return value

    def get_db_converters(self, expression):
        converters = super().get_db_converters(expression)
        internal_type = expression.output_field.get_internal_type()
        if internal_type == "DateField":
            converters.append(self.convert_datefield_value)
        elif internal_type == "DateTimeField":
            if not settings.USE_TZ:
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
            value = value.date()
        return value

    def convert_datetimefield_value(self, value, expression, connection):
        if value is not None:
            # Django expects naive datetimes when settings.USE_TZ is False.
            value = timezone.make_naive(value)
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
        """
        if getattr(field, "rel", None) is not None:
            field = field.rel.get_related_field()
        field_kind = field.get_internal_type()

        if lookup in ("in", "range"):
            return [
                self._prep_lookup_value(subvalue, field, field_kind, lookup) for subvalue in value
            ]
        return self._prep_lookup_value(value, field, field_kind, lookup)

    def _prep_lookup_value(self, value, field, field_kind, lookup):
        if value is None:
            return None

        if field_kind == "DecimalField":
            value = self.adapt_decimalfield_value(value, field.max_digits, field.decimal_places)
        return value
