from django.core.exceptions import EmptyResultSet, FieldDoesNotExist, FullResultSet
from django.db import DatabaseError, IntegrityError, NotSupportedError
from django.db.models import Count, Expression
from django.db.models.aggregates import Aggregate
from django.db.models.constants import LOOKUP_SEP
from django.db.models.sql import compiler
from django.db.models.sql.constants import GET_ITERATOR_CHUNK_SIZE, MULTI
from django.utils.functional import cached_property

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

        columns = self.get_columns()
        try:
            query = self.build_query(
                # Avoid $project (columns=None) if unneeded.
                columns if self.query.annotations or not self.query.default_cols else None
            )
        except EmptyResultSet:
            return iter([]) if result_type == MULTI else None

        return (
            (self._make_result(row, columns) for row in query.fetch())
            if result_type == MULTI
            else self._make_result(next(query.fetch()), columns)
        )

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
        if results is None:
            # QuerySet.values() or values_list()
            results = self.execute_sql(MULTI, chunked_fetch=chunked_fetch, chunk_size=chunk_size)

        fields = [s[0] for s in self.select[0 : self.col_count]]
        converters = self.get_converters(fields)
        rows = results
        if converters:
            rows = self.apply_converters(rows, converters)
        if tuple_expected:
            rows = map(tuple, rows)
        return rows

    def has_results(self):
        return bool(self.get_count(check_exists=True))

    def _make_result(self, entity, columns):
        """
        Decode values for the given fields from the database entity.

        The entity is assumed to be a dict using field database column
        names as keys.
        """
        result = []
        for name, col in columns:
            column_alias = getattr(col, "alias", None)
            obj = (
                # Use the related object...
                entity.get(column_alias, {})
                # ...if this column refers to an object for select_related().
                if column_alias is not None and column_alias != self.collection_name
                else entity
            )
            result.append(obj.get(name, col.field.get_default()))
        return result

    def check_query(self):
        """Check if the current query is supported by the database."""
        if self.query.is_empty():
            raise EmptyResultSet()
        if self.query.distinct:
            # This is a heuristic to detect QuerySet.datetimes() and dates().
            # "datetimefield" and "datefield" are the names of the annotations
            # the methods use. A user could annotate with the same names which
            # would give an incorrect error message.
            if "datetimefield" in self.query.annotations:
                raise NotSupportedError("QuerySet.datetimes() is not supported on MongoDB.")
            if "datefield" in self.query.annotations:
                raise NotSupportedError("QuerySet.dates() is not supported on MongoDB.")
            raise NotSupportedError("QuerySet.distinct() is not supported on MongoDB.")
        if self.query.extra:
            raise NotSupportedError("QuerySet.extra() is not supported on MongoDB.")
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
        kwargs = {}
        # If this query is sliced, the limits will be set on the subquery.
        inner_query = getattr(self.query, "inner_query", None)
        low_mark = inner_query.low_mark if inner_query else 0
        high_mark = inner_query.high_mark if inner_query else None
        if low_mark > 0:
            kwargs["skip"] = low_mark
        if check_exists:
            kwargs["limit"] = 1
        elif high_mark is not None:
            kwargs["limit"] = high_mark - low_mark
        try:
            return self.build_query().count(**kwargs)
        except EmptyResultSet:
            return 0

    def build_query(self, columns=None):
        """Check if the query is supported and prepare a MongoQuery."""
        self.check_query()
        query = self.query_class(self, columns)
        query.lookup_pipeline = self.get_lookup_pipeline()
        try:
            query.mongo_query = {"$expr": self.query.where.as_mql(self, self.connection)}
        except FullResultSet:
            query.mongo_query = {}
        query.order_by(self._get_ordering())
        return query

    def get_columns(self):
        """
        Return a tuple of (name, expression) with the columns and annotations
        which should be loaded by the query.
        """
        select_mask = self.query.get_select_mask()
        columns = (
            self.get_default_columns(select_mask) if self.query.default_cols else self.query.select
        )
        # Populate QuerySet.select_related() data.
        related_columns = []
        if self.query.select_related:
            self.get_related_selections(related_columns, select_mask)
            if related_columns:
                related_columns, _ = zip(*related_columns, strict=True)

        annotation_idx = 1

        def project_field(column):
            nonlocal annotation_idx
            if hasattr(column, "target"):
                # column is a Col.
                target = column.target.column
            else:
                # column is a Transform in values()/values_list() that needs a
                # name for $proj.
                target = f"__annotation{annotation_idx}"
                annotation_idx += 1
            return target, column

        return (
            tuple(map(project_field, columns))
            + tuple(self.query.annotation_select.items())
            + tuple(map(project_field, related_columns))
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

        column_ordering = []
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

            try:
                column = opts.get_field(name).column
            except FieldDoesNotExist:
                # `name` is an annotation in $project.
                column = name
            column_ordering.append((column, ascending))
        return column_ordering

    @cached_property
    def collection_name(self):
        return self.query.get_meta().db_table

    def get_collection(self):
        return self.connection.get_collection(self.collection_name)

    def get_lookup_pipeline(self):
        result = []
        for alias in tuple(self.query.alias_map):
            if not self.query.alias_refcount[alias] or self.collection_name == alias:
                continue
            result += self.query.alias_map[alias].as_mql(self, self.connection)
        return result


class SQLInsertCompiler(SQLCompiler):
    def execute_sql(self, returning_fields=None):
        self.pre_sql_setup()
        objs = []
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
            objs.append(field_values)
        return [self.insert(objs, returning_fields=returning_fields)]

    @wrap_database_errors
    def insert(self, docs, returning_fields=None):
        """Store a list of documents using field columns as element names."""
        collection = self.get_collection()
        options = self.connection.operation_flags.get("save", {})
        inserted_ids = collection.insert_many(docs, **options).inserted_ids
        return inserted_ids if returning_fields else []


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
        spec = {}
        for field, value in values:
            if field.primary_key:
                raise DatabaseError("Cannot modify _id.")
            if isinstance(value, Expression):
                raise NotSupportedError("QuerySet.update() with expression not supported.")
            # .update(foo=123) --> {'$set': {'foo': 123}}
            spec.setdefault("$set", {})[field.column] = value
        return self.execute_update(spec)

    @wrap_database_errors
    def execute_update(self, update_spec, **kwargs):
        collection = self.get_collection()
        try:
            criteria = self.build_query().mongo_query
        except EmptyResultSet:
            return 0
        options = self.connection.operation_flags.get("update", {})
        options = dict(options, **kwargs)
        return collection.update_many(criteria, update_spec, **options).matched_count


class SQLAggregateCompiler(SQLCompiler):
    pass
