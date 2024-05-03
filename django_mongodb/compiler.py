from django.conf import settings
from django.core.exceptions import EmptyResultSet
from django.db import (
    DatabaseError,
    IntegrityError,
    NotSupportedError,
    connections,
)
from django.db.models import NOT_PROVIDED, Count, Expression
from django.db.models.aggregates import Aggregate
from django.db.models.constants import LOOKUP_SEP
from django.db.models.sql import compiler
from django.db.models.sql.constants import GET_ITERATOR_CHUNK_SIZE, MULTI

from .base import Cursor
from .query import MongoQuery, wrap_database_errors


class SQLCompiler(compiler.SQLCompiler):
    """Base class for all Mongo compilers."""

    query_class = MongoQuery

    def execute_sql(
        self, result_type=MULTI, chunked_fetch=False, chunk_size=GET_ITERATOR_CHUNK_SIZE
    ):
        self.pre_sql_setup()
        # QuerySet.count()
        if self.query.annotations == {"__count": Count("*")}:
            return [self.get_count()]
        try:
            query = self.build_query()
        except EmptyResultSet:
            return None
        return query.fetch()

    def results_iter(
        self,
        results=None,
        tuple_expected=False,
        chunked_fetch=False,
        chunk_size=GET_ITERATOR_CHUNK_SIZE,
    ):
        """
        Return an iterator over the results from executing query given
        to this compiler. Called by QuerySet methods.
        """
        columns = self.get_columns()

        if results is None:
            # QuerySet.values() or values_list()
            try:
                results = self.build_query(columns).fetch()
            except EmptyResultSet:
                results = []

        converters = self.get_converters(columns)
        for entity in results:
            yield self._make_result(entity, columns, converters, tuple_expected=tuple_expected)

    def has_results(self):
        return bool(self.get_count(check_exists=True))

    def get_converters(self, columns):
        converters = {}
        for column in columns:
            backend_converters = self.connection.ops.get_db_converters(column)
            field_converters = column.field.get_db_converters(self.connection)
            if backend_converters or field_converters:
                converters[column.target.column] = backend_converters + field_converters
        return converters

    def _make_result(self, entity, columns, converters, tuple_expected=False):
        """
        Decode values for the given fields from the database entity.

        The entity is assumed to be a dict using field database column
        names as keys.
        """
        result = []
        for col in columns:
            field = col.field
            column = col.target.column
            value = entity.get(column, NOT_PROVIDED)
            if value is NOT_PROVIDED:
                value = field.get_default()
            elif converters:
                # Decode values using Django's database converters API.
                for converter in converters.get(column, ()):
                    value = converter(value, col, self.connection)
            result.append(value)
        if tuple_expected:
            result = tuple(result)
        return result

    def check_query(self):
        """Check if the current query is supported by the database."""
        if self.query.is_empty():
            raise EmptyResultSet()
        if self.query.distinct:
            raise NotSupportedError("QuerySet.distinct() is not supported on MongoDB.")
        if self.query.extra:
            raise NotSupportedError("QuerySet.extra() is not supported on MongoDB.")
        if self.query.select_related:
            raise NotSupportedError("QuerySet.select_related() is not supported on MongoDB.")
        if len([a for a in self.query.alias_map if self.query.alias_refcount[a]]) > 1:
            raise NotSupportedError("Queries with multiple tables are not supported on MongoDB.")
        if any(
            isinstance(a, Aggregate) and not isinstance(a, Count)
            for a in self.query.annotations.values()
        ):
            raise NotSupportedError("QuerySet.aggregate() isn't supported on MongoDB.")

    def get_count(self, check_exists=False):
        """
        Count objects matching the current filters / constraints.

        If `check_exists` is True, only check if any object matches.
        """
        kwargs = {"limit": 1} if check_exists else {}
        try:
            return self.build_query().count(**kwargs)
        except EmptyResultSet:
            return 0

    def build_query(self, columns=None):
        """Check if the query is supported and prepare a MongoQuery."""
        self.check_query()
        self.setup_query()
        query = self.query_class(self, columns)
        query.add_filters(self.query.where)
        query.order_by(self._get_ordering())

        # This at least satisfies the most basic unit tests.
        force_debug_cursor = connections[self.using].force_debug_cursor
        if force_debug_cursor or (force_debug_cursor is None and settings.DEBUG):
            self.connection.queries_log.append({"sql": repr(query)})
        return query

    def get_columns(self):
        """Return columns which should be loaded by the query."""
        select_mask = self.query.get_select_mask()
        return (
            self.get_default_columns(select_mask) if self.query.default_cols else self.query.select
        )

    def _get_ordering(self):
        """
        Return a list of (field, ascending) tuples that the query results
        should be ordered by. If there is no field ordering defined, return
        the standard_ordering (a boolean, needed for MongoDB "$natural"
        ordering).
        """
        opts = self.query.get_meta()
        ordering = (
            self.query.order_by or opts.ordering
            if self.query.default_ordering
            else self.query.order_by
        )

        if not ordering:
            return self.query.standard_ordering

        field_ordering = []
        for order in ordering:
            if LOOKUP_SEP in order:
                raise NotSupportedError("Ordering can't span tables on MongoDB (%s)." % order)
            if order == "?":
                raise NotSupportedError("Randomized ordering isn't supported by MongoDB.")

            ascending = not order.startswith("-")
            if not self.query.standard_ordering:
                ascending = not ascending

            name = order.lstrip("+-")
            if name == "pk":
                name = opts.pk.name

            field_ordering.append((opts.get_field(name), ascending))
        return field_ordering

    def get_collection(self):
        return self.connection.get_collection(self.query.get_meta().db_table)


class SQLInsertCompiler(SQLCompiler):
    def execute_sql(self, returning_fields=None):
        self.pre_sql_setup()

        # pk_field = self.query.get_meta().pk
        keys = []
        for obj in self.query.objs:
            field_values = {}
            for field in self.query.fields:
                value = field.get_db_prep_save(
                    getattr(obj, field.attname)
                    if self.query.raw
                    else field.pre_save(obj, obj._state.adding),
                    connection=self.connection,
                )
                if value is None and not field.null and not field.primary_key:
                    raise IntegrityError(
                        "You can't set %s (a non-nullable field) to None." % field.name
                    )

                field_values[field.column] = value
            # TODO: pass the key value through db converters (use pk_field).
            keys.append(self.insert(field_values, returning_fields=returning_fields))

        return keys

    @wrap_database_errors
    def insert(self, doc, returning_fields=None):
        """Store a document using field columns as element names."""
        collection = self.get_collection()
        options = self.connection.operation_flags.get("save", {})
        inserted_id = collection.insert_one(doc, **options).inserted_id
        return [inserted_id] if returning_fields else []


class SQLDeleteCompiler(SQLCompiler):
    def execute_sql(self, result_type=MULTI):
        cursor = Cursor()
        cursor.rowcount = self.build_query([self.query.get_meta().pk]).delete()
        return cursor


class SQLUpdateCompiler(SQLCompiler):
    def execute_sql(self, result_type):
        self.pre_sql_setup()
        values = []
        for field, _, value in self.query.values:
            if hasattr(value, "prepare_database_save"):
                if field.remote_field:
                    value = value.prepare_database_save(field)
                else:
                    raise TypeError(
                        f"Tried to update field {field} with a model "
                        f"instance, {value!r}. Use a value compatible with "
                        f"{field.__class__.__name__}."
                    )
            prepared = field.get_db_prep_save(value, connection=self.connection)
            values.append((field, prepared))
        return self.update(values)

    def update(self, values):
        multi = True
        spec = {}
        for field, value in values:
            if field.primary_key:
                raise DatabaseError("Cannot modify _id.")
            if isinstance(value, Expression):
                raise NotSupportedError("QuerySet.update() with expression not supported.")
            # .update(foo=123) --> {'$set': {'foo': 123}}
            spec.setdefault("$set", {})[field.column] = value

            if field.unique:
                multi = False

        return self.execute_update(spec, multi)

    @wrap_database_errors
    def execute_update(self, update_spec, multi=True, **kwargs):
        collection = self.get_collection()
        try:
            criteria = self.build_query().mongo_query
        except EmptyResultSet:
            return 0
        options = self.connection.operation_flags.get("update", {})
        options = dict(options, **kwargs)
        method = "update_many" if multi else "update_one"
        return getattr(collection, method)(criteria, update_spec, **options).matched_count


class SQLAggregateCompiler(SQLCompiler):
    pass
