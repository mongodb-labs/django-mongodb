from functools import reduce, wraps
from operator import add as add_operator
from collections.abc import Mapping

from django.core.exceptions import EmptyResultSet, FullResultSet
from django.db import DatabaseError, IntegrityError, NotSupportedError, connections
from django.db.models import QuerySet
from django.db.models.expressions import Case, Col, When
from django.db.models.functions import Mod
from django.db.models.lookups import Exact
from django.db.models.query import BaseIterable
from django.db.models.sql.constants import INNER, GET_ITERATOR_CHUNK_SIZE
from django.db.models.sql.datastructures import Join
from django.db.models.sql.where import AND, OR, XOR, ExtraWhere, NothingNode, WhereNode
from django.utils.functional import cached_property
from pymongo.errors import BulkWriteError, DuplicateKeyError, PyMongoError


def wrap_database_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BulkWriteError as e:
            if "E11000 duplicate key error" in str(e):
                raise IntegrityError from e
            raise
        except DuplicateKeyError as e:
            raise IntegrityError from e
        except PyMongoError as e:
            raise DatabaseError from e

    return wrapper


class MongoQuery:
    """
    Compilers build a MongoQuery when they want to fetch some data. They work
    by first allowing sql.compiler.SQLCompiler to partly build a sql.Query,
    constructing a MongoQuery query on top of it, and then iterating over its
    results.

    This class provides a framework for converting the SQL constraint tree
    built by Django to a "representation" more suitable for MongoDB.
    """

    def __init__(self, compiler):
        self.compiler = compiler
        self.connection = compiler.connection
        self.ops = compiler.connection.ops
        self.query = compiler.query
        self._negated = False
        self.ordering = []
        self.collection = self.compiler.collection
        self.collection_name = self.compiler.collection_name
        self.mongo_query = getattr(compiler.query, "raw_query", {})
        self.subqueries = None
        self.lookup_pipeline = None
        self.project_fields = None
        self.aggregation_pipeline = compiler.aggregation_pipeline
        self.extra_fields = None
        self.combinator_pipeline = None
        # $lookup stage that encapsulates the pipeline for performing a nested
        # subquery.
        self.subquery_lookup = None

    def __repr__(self):
        return f"<MongoQuery: {self.mongo_query!r} ORDER {self.ordering!r}>"

    @wrap_database_errors
    def delete(self):
        """Execute a delete query."""
        if self.compiler.subqueries:
            raise NotSupportedError("Cannot use QuerySet.delete() when a subquery is required.")
        return self.collection.delete_many(self.mongo_query).deleted_count

    @wrap_database_errors
    def get_cursor(self):
        """
        Return a pymongo CommandCursor that can be iterated on to give the
        results of the query.
        """
        return self.collection.aggregate(self.get_pipeline())

    def get_pipeline(self):
        pipeline = []
        if self.lookup_pipeline:
            pipeline.extend(self.lookup_pipeline)
        for query in self.subqueries or ():
            pipeline.extend(query.get_pipeline())
        if self.mongo_query:
            pipeline.append({"$match": self.mongo_query})
        if self.aggregation_pipeline:
            pipeline.extend(self.aggregation_pipeline)
        if self.project_fields:
            pipeline.append({"$project": self.project_fields})
        if self.combinator_pipeline:
            pipeline.extend(self.combinator_pipeline)
        if self.extra_fields:
            pipeline.append({"$addFields": self.extra_fields})
        if self.ordering:
            pipeline.append({"$sort": self.ordering})
        if self.query.low_mark > 0:
            pipeline.append({"$skip": self.query.low_mark})
        if self.query.high_mark is not None:
            pipeline.append({"$limit": self.query.high_mark - self.query.low_mark})
        if self.subquery_lookup:
            table_output = self.subquery_lookup["as"]
            pipeline = [
                {"$lookup": {**self.subquery_lookup, "pipeline": pipeline}},
                {
                    "$set": {
                        table_output: {
                            "$cond": {
                                "if": {
                                    "$or": [
                                        {"$eq": [{"$type": f"${table_output}"}, "missing"]},
                                        {"$eq": [{"$size": f"${table_output}"}, 0]},
                                    ]
                                },
                                "then": {},
                                "else": {"$arrayElemAt": [f"${table_output}", 0]},
                            }
                        }
                    }
                },
            ]
        return pipeline


def extra_where(self, compiler, connection):  # noqa: ARG001
    raise NotSupportedError("QuerySet.extra() is not supported on MongoDB.")


def join(self, compiler, connection):
    lookup_pipeline = []
    lhs_fields = []
    rhs_fields = []
    # Add a join condition for each pair of joining fields.
    parent_template = "parent__field__"
    for lhs, rhs in self.join_fields:
        lhs, rhs = connection.ops.prepare_join_on_clause(
            self.parent_alias, lhs, compiler.collection_name, rhs
        )
        lhs_fields.append(lhs.as_mql(compiler, connection))
        # In the lookup stage, the reference to this column doesn't include
        # the collection name.
        rhs_fields.append(rhs.as_mql(compiler, connection))
    # Handle any join conditions besides matching field pairs.
    extra = self.join_field.get_extra_restriction(self.table_alias, self.parent_alias)
    if extra:
        columns = []
        for expr in extra.leaves():
            # Determine whether the column needs to be transformed or rerouted
            # as part of the subquery.
            for hand_side in ["lhs", "rhs"]:
                hand_side_value = getattr(expr, hand_side, None)
                if isinstance(hand_side_value, Col):
                    # If the column is not part of the joined table, add it to
                    # lhs_fields.
                    if hand_side_value.alias != self.table_alias:
                        pos = len(lhs_fields)
                        lhs_fields.append(expr.lhs.as_mql(compiler, connection))
                    else:
                        pos = None
                    columns.append((hand_side_value, pos))
        # Replace columns in the extra conditions with new column references
        # based on their rerouted positions in the join pipeline.
        replacements = {}
        for col, parent_pos in columns:
            column_target = Col(compiler.collection_name, expr.output_field.__class__())
            if parent_pos is not None:
                target_col = f"${parent_template}{parent_pos}"
                column_target.target.db_column = target_col
                column_target.target.set_attributes_from_name(target_col)
            else:
                column_target.target = col.target
            replacements[col] = column_target
        # Apply the transformed expressions in the extra condition.
        extra_condition = [extra.replace_expressions(replacements).as_mql(compiler, connection)]
    else:
        extra_condition = []

    lookup_pipeline = [
        {
            "$lookup": {
                # The right-hand table to join.
                "from": self.table_name,
                # The pipeline variables to be matched in the pipeline's
                # expression.
                "let": {
                    f"{parent_template}{i}": parent_field
                    for i, parent_field in enumerate(lhs_fields)
                },
                "pipeline": [
                    {
                        # Match the conditions:
                        #   self.table_name.field1 = parent_table.field1
                        # AND
                        #   self.table_name.field2 = parent_table.field2
                        # AND
                        #   ...
                        "$match": {
                            "$expr": {
                                "$and": [
                                    {"$eq": [f"$${parent_template}{i}", field]}
                                    for i, field in enumerate(rhs_fields)
                                ]
                                + extra_condition
                            }
                        }
                    }
                ],
                # Rename the output as table_alias.
                "as": self.table_alias,
            }
        },
    ]
    # To avoid missing data when using $unwind, an empty collection is added if
    # the join isn't an inner join. For inner joins, rows with empty arrays are
    # removed, as $unwind unrolls or unnests the array and removes the row if
    # it's empty. This is the expected behavior for inner joins. For left outer
    # joins (LOUTER), however, an empty collection is returned.
    if self.join_type != INNER:
        lookup_pipeline.append(
            {
                "$set": {
                    self.table_alias: {
                        "$cond": {
                            "if": {
                                "$or": [
                                    {"$eq": [{"$type": f"${self.table_alias}"}, "missing"]},
                                    {"$eq": [{"$size": f"${self.table_alias}"}, 0]},
                                ]
                            },
                            "then": [{}],
                            "else": f"${self.table_alias}",
                        }
                    }
                }
            }
        )
    lookup_pipeline.append({"$unwind": f"${self.table_alias}"})
    return lookup_pipeline


def where_node(self, compiler, connection):
    if self.connector == AND:
        full_needed, empty_needed = len(self.children), 1
    else:
        full_needed, empty_needed = 1, len(self.children)

    if self.connector == AND:
        operator = "$and"
    elif self.connector == XOR:
        # MongoDB doesn't support $xor, so convert:
        #   a XOR b XOR c XOR ...
        # to:
        #   (a OR b OR c OR ...) AND MOD(a + b + c + ..., 2) == 1
        # The result of an n-ary XOR is true when an odd number of operands
        # are true.
        lhs = self.__class__(self.children, OR)
        rhs_sum = reduce(
            add_operator,
            (Case(When(c, then=1), default=0) for c in self.children),
        )
        if len(self.children) > 2:
            rhs_sum = Mod(rhs_sum, 2)
        rhs = Exact(1, rhs_sum)
        return self.__class__([lhs, rhs], AND, self.negated).as_mql(compiler, connection)
    else:
        operator = "$or"

    children_mql = []
    for child in self.children:
        try:
            mql = child.as_mql(compiler, connection)
        except EmptyResultSet:
            empty_needed -= 1
        except FullResultSet:
            full_needed -= 1
        else:
            if mql:
                children_mql.append(mql)
            else:
                full_needed -= 1

        if empty_needed == 0:
            raise (FullResultSet if self.negated else EmptyResultSet)
        if full_needed == 0:
            raise (EmptyResultSet if self.negated else FullResultSet)

    if len(children_mql) == 1:
        mql = children_mql[0]
    elif len(children_mql) > 1:
        mql = {operator: children_mql} if children_mql else {}
    else:
        mql = {}

    if not mql:
        raise FullResultSet

    if self.negated and mql:
        mql = {"$not": mql}

    return mql


def register_nodes():
    ExtraWhere.as_mql = extra_where
    Join.as_mql = join
    NothingNode.as_mql = NothingNode.as_sql
    WhereNode.as_mql = where_node


class MongoQuerySet(QuerySet):
    def raw_mql(self, raw_query, params=(), translations=None, using=None):
        if using is None:
            using = self.db
        qs = RawQuerySet(
            raw_query,
            model=self.model,
            params=params,
            translations=translations,
            using=using,
        )
        return qs


class RawQuerySet:
    """
    Provide an iterator which converts the results of raw SQL queries into
    annotated model instances.
    """

    def __init__(
        self,
        raw_query,
        model=None,
        query=None,
        params=(),
        translations=None,
        using=None,
        hints=None,
    ):
        self.raw_query = raw_query
        self.model = model
        self._db = using
        self._hints = hints or {}
        self.query = query or RawQuery(sql=raw_query, using=self.db, params=params)
        self.params = params
        self.translations = translations or {}
        self._result_cache = None
        self._prefetch_related_lookups = ()
        self._prefetch_done = False

    def resolve_model_init_order(self):
        """Resolve the init field names and value positions."""
        converter = connections[self.db].introspection.identifier_converter
        model_init_fields = [
            f for f in self.model._meta.fields if converter(f.column) in self.columns
        ]
        annotation_fields = [
            (column, pos)
            for pos, column in enumerate(self.columns)
            if column not in self.model_fields
        ]
        model_init_order = [self.columns.index(converter(f.column)) for f in model_init_fields]
        model_init_names = [f.attname for f in model_init_fields]
        return model_init_names, model_init_order, annotation_fields

    def prefetch_related(self, *lookups):
        """Same as QuerySet.prefetch_related()"""
        clone = self._clone()
        if lookups == (None,):
            clone._prefetch_related_lookups = ()
        else:
            clone._prefetch_related_lookups = clone._prefetch_related_lookups + lookups
        return clone

    def _prefetch_related_objects(self):
        prefetch_related_objects(self._result_cache, *self._prefetch_related_lookups)
        self._prefetch_done = True

    def _clone(self):
        """Same as QuerySet._clone()"""
        c = self.__class__(
            self.raw_query,
            model=self.model,
            query=self.query,
            params=self.params,
            translations=self.translations,
            using=self._db,
            hints=self._hints,
        )
        c._prefetch_related_lookups = self._prefetch_related_lookups[:]
        return c

    def _fetch_all(self):
        if self._result_cache is None:
            self._result_cache = list(self.iterator())
        if self._prefetch_related_lookups and not self._prefetch_done:
            self._prefetch_related_objects()

    def __len__(self):
        self._fetch_all()
        return len(self._result_cache)

    def __bool__(self):
        self._fetch_all()
        return bool(self._result_cache)

    def __iter__(self):
        self._fetch_all()
        return iter(self._result_cache)

    def __aiter__(self):
        # Remember, __aiter__ itself is synchronous, it's the thing it returns
        # that is async!
        async def generator():
            await sync_to_async(self._fetch_all)()
            for item in self._result_cache:
                yield item

        return generator()

    def iterator(self):
        yield from RawModelIterable(self)

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.query)

    def __getitem__(self, k):
        return list(self)[k]

    @property
    def db(self):
        """Return the database used if this query is executed now."""
        return self._db or router.db_for_read(self.model, **self._hints)

    def using(self, alias):
        """Select the database this RawQuerySet should execute against."""
        return RawQuerySet(
            self.raw_query,
            model=self.model,
            query=self.query.chain(using=alias),
            params=self.params,
            translations=self.translations,
            using=alias,
        )

    @cached_property
    def columns(self):
        """
        A list of model field names in the order they'll appear in the
        query results.
        """
        columns = self.query.get_columns()
        # Adjust any column names which don't match field names
        for query_name, model_name in self.translations.items():
            # Ignore translations for nonexistent column names
            try:
                index = columns.index(query_name)
            except ValueError:
                pass
            else:
                columns[index] = model_name
        return columns

    @cached_property
    def model_fields(self):
        """A dict mapping column names to model field names."""
        converter = connections[self.db].introspection.identifier_converter
        model_fields = {}
        for field in self.model._meta.fields:
            name, column = field.get_attname_column()
            model_fields[converter(column)] = field
        return model_fields


class RawQuery:
    """A single raw SQL query."""

    def __init__(self, sql, using, params=()):
        self.params = params
        self.sql = sql
        self.using = using
        self.cursor = None

        # Mirror some properties of a normal query so that
        # the compiler can be used to process results.
        self.low_mark, self.high_mark = 0, None  # Used for offset/limit
        self.extra_select = {}
        self.annotation_select = {}

    def chain(self, using):
        return self.clone(using)

    def clone(self, using):
        return RawQuery(self.sql, using, params=self.params)

    def get_columns(self):
        if self.cursor is None:
            self._execute_query()
        converter = connections[self.using].introspection.identifier_converter
        return [converter(column_meta[0]) for column_meta in self.cursor.description]

    def __iter__(self):
        # Always execute a new query for a new iterator.
        # This could be optimized with a cache at the expense of RAM.
        self._execute_query()
        if not connections[self.using].features.can_use_chunked_reads:
            # If the database can't use chunked reads we need to make sure we
            # evaluate the entire query up front.
            result = list(self.cursor)
        else:
            result = self.cursor
        return iter(result)

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self)

    @property
    def params_type(self):
        if self.params is None:
            return None
        return dict if isinstance(self.params, Mapping) else tuple

    def __str__(self):
        if self.params_type is None:
            return self.sql
        return self.sql % self.params_type(self.params)

    def _execute_query(self):
        connection = connections[self.using]

        # Adapt parameters to the database, as much as possible considering
        # that the target type isn't known. See #17755.
        params_type = self.params_type
        adapter = connection.ops.adapt_unknown_value
        if params_type is tuple:
            params = tuple(adapter(val) for val in self.params)
        elif params_type is dict:
            params = {key: adapter(val) for key, val in self.params.items()}
        elif params_type is None:
            params = None
        else:
            raise RuntimeError("Unexpected params type: %s" % params_type)

        self.cursor = connection.cursor()
        self.cursor.execute(self.sql, params)


class RawModelIterable(BaseIterable):
    """
    Iterable that yields a model instance for each row from a raw queryset.
    """

    def __iter__(self):
        # Cache some things for performance reasons outside the loop.
        db = self.queryset.db
        query = self.queryset.query
        connection = connections[db]
        compiler = connection.ops.compiler("SQLCompiler")(query, connection, db)
        query_iterator = iter(query)

        try:
            (
                model_init_names,
                model_init_pos,
                annotation_fields,
            ) = self.queryset.resolve_model_init_order()
            model_cls = self.queryset.model
            if model_cls._meta.pk.attname not in model_init_names:
                raise exceptions.FieldDoesNotExist("Raw query must include the primary key")
            fields = [self.queryset.model_fields.get(c) for c in self.queryset.columns]
            converters = compiler.get_converters(
                [f.get_col(f.model._meta.db_table) if f else None for f in fields]
            )
            if converters:
                query_iterator = compiler.apply_converters(query_iterator, converters)
            for values in query_iterator:
                # Associate fields to values
                model_init_values = [values[pos] for pos in model_init_pos]
                instance = model_cls.from_db(db, model_init_names, model_init_values)
                if annotation_fields:
                    for column, pos in annotation_fields:
                        setattr(instance, column, values[pos])
                yield instance
        finally:
            # Done iterating the Query. If it has its own cursor, close it.
            if hasattr(query, "cursor") and query.cursor:
                query.cursor.close()
