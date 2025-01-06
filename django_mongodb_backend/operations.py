import datetime
import json
import re
import uuid
from decimal import Decimal

from bson.decimal128 import Decimal128
from django.conf import settings
from django.db import DataError
from django.db.backends.base.operations import BaseDatabaseOperations
from django.db.models import TextField
from django.db.models.expressions import Combinable
from django.db.models.functions import Cast
from django.utils import timezone
from django.utils.regex_helper import _lazy_re_compile


class DatabaseOperations(BaseDatabaseOperations):
    compiler_module = "django_mongodb_backend.compiler"
    combine_operators = {
        Combinable.ADD: "add",
        Combinable.SUB: "subtract",
        Combinable.MUL: "multiply",
        Combinable.DIV: "divide",
        Combinable.POW: "pow",
        Combinable.MOD: "mod",
        Combinable.BITAND: "bitAnd",
        Combinable.BITOR: "bitOr",
        Combinable.BITXOR: "bitXor",
    }
    explain_options = {"comment", "verbosity"}

    def adapt_datefield_value(self, value):
        """Store DateField as datetime."""
        if value is None:
            return None
        return datetime.datetime.combine(value, datetime.datetime.min.time())

    def adapt_datetimefield_value(self, value):
        if value is None:
            return None
        # Expression values are adapted by the database.
        if hasattr(value, "resolve_expression"):
            return value
        if timezone.is_aware(value):
            if settings.USE_TZ:
                value = timezone.make_naive(value, self.connection.timezone)
            else:
                raise ValueError(
                    "MongoDB backend does not support timezone-aware "
                    "datetimes when USE_TZ is False."
                )
        return value

    def adapt_decimalfield_value(self, value, max_digits=None, decimal_places=None):
        """Store DecimalField as Decimal128."""
        if value is None:
            return None
        return Decimal128(value)

    def adapt_json_value(self, value, encoder):
        if encoder is None:
            return value
        try:
            return json.loads(json.dumps(value, cls=encoder))
        except json.decoder.JSONDecodeError as e:
            raise DataError from e

    def adapt_timefield_value(self, value):
        """Store TimeField as datetime."""
        if value is None:
            return None
        # Expression values are adapted by the database.
        if hasattr(value, "resolve_expression"):
            return value
        if timezone.is_aware(value):
            raise ValueError("MongoDB backend does not support timezone-aware times.")
        return datetime.datetime.combine(datetime.datetime.min.date(), value)

    def get_db_converters(self, expression):
        converters = super().get_db_converters(expression)
        internal_type = expression.output_field.get_internal_type()
        if internal_type == "DateField":
            converters.append(self.convert_datefield_value)
        elif internal_type == "DateTimeField":
            if settings.USE_TZ:
                converters.append(self.convert_datetimefield_value)
        elif internal_type == "DecimalField":
            converters.append(self.convert_decimalfield_value)
        elif internal_type == "JSONField":
            converters.append(self.convert_jsonfield_value)
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
            value = timezone.make_aware(value, self.connection.timezone)
        return value

    def convert_decimalfield_value(self, value, expression, connection):
        if value is not None:
            # from Decimal128 to decimal.Decimal()
            try:
                value = value.to_decimal()
            except AttributeError:
                # `value` could be an integer in the case of an annotation
                # like ExpressionWrapper(Value(1), output_field=DecimalField().
                return Decimal(value)
        return value

    def convert_durationfield_value(self, value, expression, connection):
        if value is not None:
            try:
                value = datetime.timedelta(milliseconds=value)
            except TypeError:
                # `value` could be Decimal128 if doing a computation with
                # DurationField and Decimal128.
                value = datetime.timedelta(milliseconds=int(str(value)))
        return value

    def convert_jsonfield_value(self, value, expression, connection):
        """
        Convert dict data to a string so that JSONField.from_db_value() can
        decode it using json.loads().
        """
        return json.dumps(value)

    def convert_timefield_value(self, value, expression, connection):
        if value is not None:
            value = value.time()
        return value

    def convert_uuidfield_value(self, value, expression, connection):
        if value is not None:
            value = uuid.UUID(value)
        return value

    def combine_expression(self, connector, sub_expressions):
        lhs, rhs = sub_expressions
        if connector == Combinable.BITLEFTSHIFT:
            return {"$multiply": [lhs, {"$pow": [2, rhs]}]}
        if connector == Combinable.BITRIGHTSHIFT:
            return {"$floor": {"$divide": [lhs, {"$pow": [2, rhs]}]}}
        operator = self.combine_operators[connector]
        return {f"${operator}": sub_expressions}

    def prep_for_like_query(self, x):
        """Escape "x" for $regexMatch queries."""
        return re.escape(x)

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
                collection.delete_many({})

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

    def explain_query_prefix(self, format=None, **options):
        # Validate options.
        validated_options = {}
        if options:
            for valid_option in self.explain_options:
                value = options.pop(valid_option, None)
                if value is not None:
                    validated_options[valid_option] = value
        # super() raises an error if any options are left after the valid ones
        # are popped above.
        super().explain_query_prefix(format, **options)
        return validated_options

    def integer_field_range(self, internal_type):
        # MongODB doesn't enforce any integer constraints, but it supports
        # integers up to 64 bits.
        if internal_type in {
            "PositiveBigIntegerField",
            "PositiveIntegerField",
            "PositiveSmallIntegerField",
        }:
            return (0, 9223372036854775807)
        return (-9223372036854775808, 9223372036854775807)

    def prepare_join_on_clause(self, lhs_table, lhs_field, rhs_table, rhs_field):
        lhs_expr, rhs_expr = super().prepare_join_on_clause(
            lhs_table, lhs_field, rhs_table, rhs_field
        )
        # If the types are different, cast both to string.
        if lhs_field.db_type(self.connection) != rhs_field.db_type(self.connection):
            if lhs_field.db_type(self.connection) != "string":
                lhs_expr = Cast(lhs_expr, output_field=TextField())
            if rhs_field.db_type(self.connection) != "string":
                rhs_expr = Cast(rhs_expr, output_field=TextField())
        return lhs_expr, rhs_expr

    """Django uses these methods to generate SQL queries before it generates MQL queries."""

    # EXTRACT format cannot be passed in parameters.
    _extract_format_re = _lazy_re_compile(r"[A-Z_]+")

    def date_extract_sql(self, lookup_type, sql, params):
        if lookup_type == "week_day":
            # For consistency across backends, we return Sunday=1, Saturday=7.
            return f"EXTRACT(DOW FROM {sql}) + 1", params
        if lookup_type == "iso_week_day":
            return f"EXTRACT(ISODOW FROM {sql})", params
        if lookup_type == "iso_year":
            return f"EXTRACT(ISOYEAR FROM {sql})", params

        lookup_type = lookup_type.upper()
        if not self._extract_format_re.fullmatch(lookup_type):
            raise ValueError(f"Invalid lookup type: {lookup_type!r}")
        return f"EXTRACT({lookup_type} FROM {sql})", params

    def datetime_extract_sql(self, lookup_type, sql, params, tzname):
        if lookup_type == "second":
            # Truncate fractional seconds.
            return f"EXTRACT(SECOND FROM DATE_TRUNC(%s, {sql}))", ("second", *params)
        return self.date_extract_sql(lookup_type, sql, params)

    def datetime_trunc_sql(self, lookup_type, sql, params, tzname):
        return f"DATE_TRUNC(%s, {sql})", (lookup_type, *params)

    def date_trunc_sql(self, lookup_type, sql, params, tzname=None):
        return f"DATE_TRUNC(%s, {sql})", (lookup_type, *params)

    def datetime_cast_date_sql(self, sql, params, tzname):
        return f"({sql})::date", params

    def datetime_cast_time_sql(self, sql, params, tzname):
        return f"({sql})::time", params

    def format_for_duration_arithmetic(self, sql):
        return "INTERVAL %s MILLISECOND" % sql

    def time_trunc_sql(self, lookup_type, sql, params, tzname=None):
        return f"DATE_TRUNC(%s, {sql})::time", (lookup_type, *params)
