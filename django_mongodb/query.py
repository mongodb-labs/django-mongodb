from functools import reduce, wraps
from operator import add as add_operator

from django.core.exceptions import EmptyResultSet, FullResultSet
from django.db import DatabaseError, IntegrityError
from django.db.models.expressions import Case, When
from django.db.models.functions import Mod
from django.db.models.lookups import Exact
from django.db.models.sql.constants import INNER
from django.db.models.sql.datastructures import Join
from django.db.models.sql.where import AND, OR, XOR, NothingNode, WhereNode
from pymongo.errors import DuplicateKeyError, PyMongoError


def wrap_database_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
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
        self.collection = self.compiler.get_collection()
        self.collection_name = self.compiler.collection_name
        self.mongo_query = getattr(compiler.query, "raw_query", {})
        self.subquery = None
        self.lookup_pipeline = None
        self.project_fields = None
        self.aggregation_pipeline = compiler.aggregation_pipeline
        self.extra_fields = None

    def __repr__(self):
        return f"<MongoQuery: {self.mongo_query!r} ORDER {self.ordering!r}>"

    @wrap_database_errors
    def delete(self):
        """Execute a delete query."""
        return self.collection.delete_many(self.mongo_query).deleted_count

    @wrap_database_errors
    def get_cursor(self):
        """
        Return a pymongo CommandCursor that can be iterated on to give the
        results of the query.
        """
        return self.collection.aggregate(self.get_pipeline())

    def get_pipeline(self):
        pipeline = self.subquery.get_pipeline() if self.subquery else []
        if self.lookup_pipeline:
            pipeline.extend(self.lookup_pipeline)
        if self.mongo_query:
            pipeline.append({"$match": self.mongo_query})
        if self.aggregation_pipeline:
            pipeline.extend(self.aggregation_pipeline)
        if self.project_fields:
            pipeline.append({"$project": self.project_fields})
        if self.extra_fields:
            pipeline.append({"$addFields": self.extra_fields})
        if self.ordering:
            pipeline.append({"$sort": self.ordering})
        if self.query.low_mark > 0:
            pipeline.append({"$skip": self.query.low_mark})
        if self.query.high_mark is not None:
            pipeline.append({"$limit": self.query.high_mark - self.query.low_mark})
        return pipeline


def join(self, compiler, connection):
    lookup_pipeline = []
    lhs_fields = []
    rhs_fields = []
    # Add a join condition for each pair of joining fields.
    for lhs, rhs in self.join_fields:
        lhs, rhs = connection.ops.prepare_join_on_clause(
            self.parent_alias, lhs, self.table_name, rhs
        )
        lhs_fields.append(lhs.as_mql(compiler, connection))
        # In the lookup stage, the reference to this column doesn't include
        # the collection name.
        rhs_fields.append(rhs.as_mql(compiler, connection).replace(f"{self.table_name}.", "", 1))

    parent_template = "parent__field__"
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
        mql = {"$eq": [mql, {"$literal": False}]}

    return mql


def register_nodes():
    Join.as_mql = join
    NothingNode.as_mql = NothingNode.as_sql
    WhereNode.as_mql = where_node
