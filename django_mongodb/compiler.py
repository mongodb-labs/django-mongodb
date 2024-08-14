import itertools
from collections import defaultdict

from bson import SON
from django.core.exceptions import EmptyResultSet, FullResultSet
from django.db import DatabaseError, IntegrityError, NotSupportedError
from django.db.models import Count, Expression
from django.db.models.aggregates import Aggregate, Variance
from django.db.models.expressions import Case, Col, Ref, Value, When
from django.db.models.functions.comparison import Coalesce
from django.db.models.functions.math import Power
from django.db.models.lookups import IsNull
from django.db.models.sql import compiler
from django.db.models.sql.constants import GET_ITERATOR_CHUNK_SIZE, MULTI, SINGLE
from django.utils.functional import cached_property
from pymongo import ASCENDING, DESCENDING

from .base import Cursor
from .query import MongoQuery, wrap_database_errors


class SQLCompiler(compiler.SQLCompiler):
    """Base class for all Mongo compilers."""

    query_class = MongoQuery
    GROUP_SEPARATOR = "___"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.aggregation_pipeline = None
        # A list of OrderBy objects for this query.
        self.order_by_objs = None

    def _get_group_alias_column(self, expr, annotation_group_idx):
        """Generate a dummy field for use in the ids fields in $group."""
        replacement = None
        if isinstance(expr, Col):
            col = expr
        else:
            # If the column is a composite expression, create a field for it.
            alias = f"__annotation_group{next(annotation_group_idx)}"
            col = self._get_column_from_expression(expr, alias)
            replacement = col
        if self.collection_name == col.alias:
            return col.target.column, replacement
        # If this is a foreign field, replace the normal dot (.) with
        # GROUP_SEPARATOR since FieldPath field names may not contain '.'.
        return f"{col.alias}{self.GROUP_SEPARATOR}{col.target.column}", replacement

    def _get_column_from_expression(self, expr, alias):
        """
        Create a column named `alias` from the given expression to hold the
        aggregate value.
        """
        column_target = expr.output_field.__class__()
        column_target.db_column = alias
        column_target.set_attributes_from_name(alias)
        return Col(self.collection_name, column_target)

    def _prepare_expressions_for_pipeline(self, expression, target, annotation_group_idx):
        """
        Prepare expressions for the aggregation pipeline.

        Handle the computation of aggregation functions used by various
        expressions. Separate and create intermediate columns, and replace
        nodes to simulate a group by operation.

        MongoDB's $group stage doesn't allow operations over the aggregator,
        e.g. COALESCE(AVG(field), 3). However, it supports operations inside
        the aggregation, e.g. AVG(number * 2).

        Handle the first case by splitting the computation into stages: compute
        the aggregation first, then apply additional operations in a subsequent
        stage by replacing the aggregate expressions with new columns prefixed
        by `__aggregation`.
        """
        replacements = {}
        group = {}
        for sub_expr in self._get_aggregate_expressions(expression):
            alias = (
                f"__aggregation{next(annotation_group_idx)}" if sub_expr != expression else target
            )
            column_target = sub_expr.output_field.__class__()
            column_target.db_column = alias
            column_target.set_attributes_from_name(alias)
            inner_column = Col(self.collection_name, column_target)
            if sub_expr.distinct:
                # If the expression should return distinct values, use
                # $addToSet to deduplicate.
                rhs = sub_expr.as_mql(self, self.connection, resolve_inner_expression=True)
                group[alias] = {"$addToSet": rhs}
                replacing_expr = sub_expr.copy()
                replacing_expr.set_source_expressions([inner_column])
            else:
                group[alias] = sub_expr.as_mql(self, self.connection)
                replacing_expr = inner_column
            # Count must return 0 rather than null.
            if isinstance(sub_expr, Count):
                replacing_expr = Coalesce(replacing_expr, 0)
            # Variance = StdDev^2
            if isinstance(sub_expr, Variance):
                replacing_expr = Power(replacing_expr, 2)
            replacements[sub_expr] = replacing_expr
        return replacements, group

    def _prepare_annotations_for_aggregation_pipeline(self, order_by):
        """Prepare annotations for the aggregation pipeline."""
        replacements = {}
        group = {}
        annotation_group_idx = itertools.count(start=1)
        for target, expr in self.query.annotation_select.items():
            if expr.contains_aggregate:
                new_replacements, expr_group = self._prepare_expressions_for_pipeline(
                    expr, target, annotation_group_idx
                )
                replacements.update(new_replacements)
                group.update(expr_group)
        for expr, _ in order_by:
            if expr.contains_aggregate:
                new_replacements, expr_group = self._prepare_expressions_for_pipeline(
                    expr, None, annotation_group_idx
                )
                replacements.update(new_replacements)
                group.update(expr_group)
        having_replacements, having_group = self._prepare_expressions_for_pipeline(
            self.having, None, annotation_group_idx
        )
        replacements.update(having_replacements)
        group.update(having_group)
        return group, replacements

    def _get_group_id_expressions(self, order_by):
        """Generate group ID expressions for the aggregation pipeline."""
        group_expressions = set()
        replacements = {}
        if not self._meta_ordering:
            for expr, (_, _, is_ref) in order_by:
                if not is_ref:
                    group_expressions |= set(expr.get_group_by_cols())
        for expr, *_ in self.select:
            group_expressions |= set(expr.get_group_by_cols())
        having_group_by = self.having.get_group_by_cols() if self.having else ()
        for expr in having_group_by:
            group_expressions.add(expr)
        if isinstance(self.query.group_by, tuple | list):
            group_expressions |= set(self.query.group_by)
        elif self.query.group_by is None:
            group_expressions = set()
        if not group_expressions:
            ids = None
        else:
            annotation_group_idx = itertools.count(start=1)
            ids = {}
            for col in group_expressions:
                alias, replacement = self._get_group_alias_column(col, annotation_group_idx)
                try:
                    ids[alias] = col.as_mql(self, self.connection)
                except EmptyResultSet:
                    ids[alias] = Value(False).as_mql(self, self.connection)
                except FullResultSet:
                    ids[alias] = Value(True).as_mql(self, self.connection)
                if replacement is not None:
                    replacements[col] = replacement
        return ids, replacements

    def _build_aggregation_pipeline(self, ids, group):
        """Build the aggregation pipeline for grouping."""
        pipeline = []
        if not ids:
            group["_id"] = None
            pipeline.append({"$facet": {"group": [{"$group": group}]}})
            pipeline.append(
                {
                    "$addFields": {
                        key: {
                            "$getField": {
                                "input": {"$arrayElemAt": ["$group", 0]},
                                "field": key,
                            }
                        }
                        for key in group
                    }
                }
            )
        else:
            group["_id"] = ids
            pipeline.append({"$group": group})
            projected_fields = defaultdict(dict)
            for key in ids:
                value = f"$_id.{key}"
                if self.GROUP_SEPARATOR in key:
                    table, field = key.split(self.GROUP_SEPARATOR)
                    projected_fields[table][field] = value
                else:
                    projected_fields[key] = value
            # Convert defaultdict to dict so it doesn't appear as
            # "defaultdict(<CLASS 'dict'>, ..." in query logging.
            pipeline.append({"$addFields": dict(projected_fields)})
            if "_id" not in projected_fields:
                pipeline.append({"$unset": "_id"})
        return pipeline

    def pre_sql_setup(self, with_col_aliases=False):
        extra_select, order_by, group_by = super().pre_sql_setup(with_col_aliases=with_col_aliases)
        group, all_replacements = self._prepare_annotations_for_aggregation_pipeline(order_by)
        # query.group_by is either:
        # - None: no GROUP BY
        # - True: group by select fields
        # - a list of expressions to group by.
        if group or self.query.group_by:
            ids, replacements = self._get_group_id_expressions(order_by)
            all_replacements.update(replacements)
            pipeline = self._build_aggregation_pipeline(ids, group)
            if self.having:
                pipeline.append(
                    {
                        "$match": {
                            "$expr": self.having.replace_expressions(all_replacements).as_mql(
                                self, self.connection
                            )
                        }
                    }
                )
            self.aggregation_pipeline = pipeline
        self.annotations = {
            target: expr.replace_expressions(all_replacements)
            for target, expr in self.query.annotation_select.items()
        }
        self.order_by_objs = [expr.replace_expressions(all_replacements) for expr, _ in order_by]
        return extra_select, order_by, group_by

    def execute_sql(
        self, result_type=MULTI, chunked_fetch=False, chunk_size=GET_ITERATOR_CHUNK_SIZE
    ):
        self.pre_sql_setup()
        columns = self.get_columns()
        try:
            query = self.build_query(
                # Avoid $project (columns=None) if unneeded.
                columns if self.query.annotations or not self.query.default_cols else None
            )
        except EmptyResultSet:
            return iter([]) if result_type == MULTI else None

        cursor = query.get_cursor()
        if result_type == SINGLE:
            try:
                obj = cursor.next()
            except StopIteration:
                return None  # No result
            else:
                return self._make_result(obj, columns)
        # result_type is MULTI
        cursor.batch_size(chunk_size)
        result = self.cursor_iter(cursor, chunk_size, columns)
        if not chunked_fetch:
            # If using non-chunked reads, read data into memory.
            return list(result)
        return result

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

        This method is copied from the superclass with one modification: the
        `if tuple_expected` block is deindented so that the result of
        _make_result() (a list) is cast to tuple as needed. For SQL database
        drivers, tuple results come from cursor.fetchmany(), so the cast is
        only needed there when apply_converters() casts the tuple to a list.
        This customized method could be removed if _make_result() cast its
        return value to a tuple, but that would be more expensive since that
        cast is not always needed.
        """
        if results is None:
            # QuerySet.values() or values_list()
            results = self.execute_sql(MULTI, chunked_fetch=chunked_fetch, chunk_size=chunk_size)

        fields = [s[0] for s in self.select[0 : self.col_count]]
        converters = self.get_converters(fields)
        rows = itertools.chain.from_iterable(results)
        if converters:
            rows = self.apply_converters(rows, converters)
        if tuple_expected:
            rows = map(tuple, rows)
        return rows

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
            result.append(obj.get(name))
        return result

    def cursor_iter(self, cursor, chunk_size, columns):
        """Yield chunks of results from cursor."""
        chunk = []
        for row in cursor:
            chunk.append(self._make_result(row, columns))
            if len(chunk) == chunk_size:
                yield chunk
                chunk = []
        yield chunk

    def check_query(self):
        """Check if the current query is supported by the database."""
        if self.query.distinct or getattr(
            # In the case of Query.distinct().count(), the distinct attribute
            # will be set on the inner_query.
            getattr(self.query, "inner_query", None),
            "distinct",
            None,
        ):
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
            if any(key.startswith("_prefetch_related_") for key in self.query.extra):
                raise NotSupportedError("QuerySet.prefetch_related() is not supported on MongoDB.")
            raise NotSupportedError("QuerySet.extra() is not supported on MongoDB.")

    def build_query(self, columns=None):
        """Check if the query is supported and prepare a MongoQuery."""
        self.check_query()
        query = self.query_class(self)
        query.lookup_pipeline = self.get_lookup_pipeline()
        ordering_fields, sort_ordering, extra_fields = self._get_ordering()
        query.project_fields = self.get_project_fields(columns, ordering_fields)
        query.ordering = sort_ordering
        # If columns is None, then get_project_fields() won't add
        # ordering_fields to $project. Use $addFields (extra_fields) instead.
        if columns is None:
            extra_fields += ordering_fields
        if extra_fields:
            query.extra_fields = {
                field_name: expr.as_mql(self, self.connection) for field_name, expr in extra_fields
            }
        where = self.get_where()
        try:
            expr = where.as_mql(self, self.connection) if where else {}
        except FullResultSet:
            query.mongo_query = {}
        else:
            query.mongo_query = {"$expr": expr}
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
            + tuple(self.annotations.items())
            + tuple(map(project_field, related_columns))
        )

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

    def _get_aggregate_expressions(self, expr):
        stack = [expr]
        while stack:
            expr = stack.pop()
            if isinstance(expr, Aggregate):
                yield expr
            elif hasattr(expr, "get_source_expressions"):
                stack.extend(expr.get_source_expressions())

    def get_project_fields(self, columns=None, ordering=None):
        fields = defaultdict(dict)
        for name, expr in columns or []:
            collection = expr.alias if isinstance(expr, Col) else None
            try:
                fields[collection][name] = (
                    1
                    # For brevity/simplicity, project {"field_name": 1}
                    # instead of {"field_name": "$field_name"}.
                    if isinstance(expr, Col) and name == expr.target.column
                    else expr.as_mql(self, self.connection)
                )
            except EmptyResultSet:
                fields[collection][name] = Value(False).as_mql(self, self.connection)
            except FullResultSet:
                fields[collection][name] = Value(True).as_mql(self, self.connection)
        # Annotations (stored in None) and the main collection's fields
        # should appear in the top-level of the fields dict.
        fields.update(fields.pop(None, {}))
        fields.update(fields.pop(self.collection_name, {}))
        # Add order_by() fields.
        if fields and ordering:
            fields.update({alias: expr.as_mql(self, self.connection) for alias, expr in ordering})
        # Convert defaultdict to dict so it doesn't appear as
        # "defaultdict(<CLASS 'dict'>, ..." in query logging.
        return dict(fields)

    def _get_ordering(self):
        """
        Process the query's OrderBy objects and return:
        - A tuple of ('field_name': Col/Expression, ...)
        - A bson.SON mapping to pass to $sort.
        - A tuple of ('field_name': Expression, ...) for expressions that need
          to be added to extra_fields.
        """
        fields = {}
        sort_ordering = SON()
        extra_fields = {}
        idx = itertools.count(start=1)
        for order in self.order_by_objs or []:
            if isinstance(order.expression, Col):
                field_name = order.expression.as_mql(self, self.connection).removeprefix("$")
                fields[field_name] = order.expression
            elif isinstance(order.expression, Ref):
                field_name = order.expression.as_mql(self, self.connection).removeprefix("$")
            else:
                field_name = f"__order{next(idx)}"
                fields[field_name] = order.expression
            # If the expression is ordered by NULLS FIRST or NULLS LAST,
            # add a field for sorting that's 1 if null or 0 if not.
            if order.nulls_first or order.nulls_last:
                null_fieldname = f"__order{next(idx)}"
                condition = When(IsNull(order.expression, True), then=Value(1))
                extra_fields[null_fieldname] = Case(condition, default=Value(0))
                sort_ordering[null_fieldname] = DESCENDING if order.nulls_first else ASCENDING
            sort_ordering[field_name] = DESCENDING if order.descending else ASCENDING
        return tuple(fields.items()), sort_ordering, tuple(extra_fields.items())

    def get_where(self):
        return self.where


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


class SQLDeleteCompiler(compiler.SQLDeleteCompiler, SQLCompiler):
    def execute_sql(self, result_type=MULTI):
        cursor = Cursor()
        cursor.rowcount = self.build_query().delete()
        return cursor

    def check_query(self):
        super().check_query()
        if not self.single_alias:
            raise NotSupportedError(
                "Cannot use QuerySet.delete() when querying across multiple collections on MongoDB."
            )

    def get_where(self):
        return self.query.where


class SQLUpdateCompiler(compiler.SQLUpdateCompiler, SQLCompiler):
    def execute_sql(self, result_type):
        """
        Execute the specified update. Return the number of rows affected by
        the primary update query. The "primary update query" is the first
        non-empty query that is executed. Row counts for any subsequent,
        related queries are not available.
        """
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
        is_empty = not bool(values)
        rows = 0 if is_empty else self.update(values)
        for query in self.query.get_related_updates():
            aux_rows = query.get_compiler(self.using).execute_sql(result_type)
            if is_empty and aux_rows:
                rows = aux_rows
                is_empty = False
        return rows

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

    def check_query(self):
        super().check_query()
        if len([a for a in self.query.alias_map if self.query.alias_refcount[a]]) > 1:
            raise NotSupportedError(
                "Cannot use QuerySet.update() when querying across multiple collections on MongoDB."
            )

    def get_where(self):
        return self.query.where


class SQLAggregateCompiler(SQLCompiler):
    def build_query(self, columns=None):
        query = self.query_class(self)
        query.project_fields = self.get_project_fields(tuple(self.annotations.items()))
        compiler = self.query.inner_query.get_compiler(
            self.using,
            elide_empty=self.elide_empty,
        )
        compiler.pre_sql_setup(with_col_aliases=False)
        # Avoid $project (columns=None) if unneeded.
        columns = (
            compiler.get_columns()
            if compiler.query.annotations or not compiler.query.default_cols
            else None
        )
        subquery = compiler.build_query(columns)
        query.subquery = subquery
        return query

    def _make_result(self, result, columns=None):
        return [result[k] for k in self.query.annotation_select]
