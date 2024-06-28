from functools import wraps

from django.core.exceptions import EmptyResultSet, FullResultSet
from django.db import DatabaseError, IntegrityError
from django.db.models import Value
from django.db.models.sql.where import AND, XOR, WhereNode
from pymongo import ASCENDING, DESCENDING
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

    def __init__(self, compiler, columns):
        self.compiler = compiler
        self.connection = compiler.connection
        self.ops = compiler.connection.ops
        self.query = compiler.query
        self.columns = columns
        self._negated = False
        self.ordering = []
        self.collection_name = self.compiler.collection_name
        self.collection = self.compiler.get_collection()
        self.mongo_query = getattr(compiler.query, "raw_query", {})
        # maybe I have to create a new object or named tuple.
        # it will save lookups, some filters (in case of inner) and project to rename field
        # don't know if the rename is needed
        self.mongo_lookups = None

    def __repr__(self):
        return f"<MongoQuery: {self.mongo_query!r} ORDER {self.ordering!r}>"

    def fetch(self):
        """Return an iterator over the query results."""
        yield from self.get_cursor()

    @wrap_database_errors
    def count(self, limit=None):
        """
        Return the number of objects that would be returned, if this query was
        executed, up to `limit`.
        """
        kwargs = {"limit": limit} if limit is not None else {}
        return self.collection.count_documents(self.mongo_query, **kwargs)

    def order_by(self, ordering):
        """
        Reorder query results or execution order. Called by compiler during
        query building.

        `ordering` is a list with (field, ascending) tuples or a boolean --
        use natural ordering, if any, when the argument is True and its reverse
        otherwise.
        """
        if isinstance(ordering, bool):
            # No need to add {$natural: ASCENDING} as it's the default.
            if not ordering:
                self.ordering.append(("$natural", DESCENDING))
        else:
            for field, ascending in ordering:
                direction = ASCENDING if ascending else DESCENDING
                self.ordering.append((field.column, direction))

    @wrap_database_errors
    def delete(self):
        """Execute a delete query."""
        options = self.connection.operation_flags.get("delete", {})
        return self.collection.delete_many(self.mongo_query, **options).deleted_count

    def get_cursor(self):
        if self.query.low_mark == self.query.high_mark:
            return []
        fields = {}
        for name, expr in self.columns or []:
            try:
                column = expr.target.column
            except AttributeError:
                # Generate the MQL for an annotation.
                try:
                    fields[name] = expr.as_mql(self.compiler, self.connection)
                except EmptyResultSet:
                    fields[name] = Value(False).as_mql(self.compiler, self.connection)
                except FullResultSet:
                    fields[name] = Value(True).as_mql(self.compiler, self.connection)
            else:
                # If name != column, then this is an annotatation referencing
                # another column.
                fields[name] = 1 if name == column else f"${column}"

        # add the subquery tables. if fields is defined
        related_fields = {}
        if fields:
            for alias in self.query.alias_map:
                if self.query.alias_refcount[alias] > 0 and self.collection_name != alias:
                    related_fields[alias] = 1

        pipeline = []
        if self.mongo_lookups:
            lookups = self.mongo_lookups
            pipeline.extend(lookups)
        if self.mongo_query:
            pipeline.append({"$match": self.mongo_query})
        if fields:
            pipeline.append({"$project": {**fields, **related_fields}})
        if self.ordering:
            pipeline.append({"$sort": dict(self.ordering)})
        if self.query.low_mark > 0:
            pipeline.append({"$skip": self.query.low_mark})
        if self.query.high_mark is not None:
            pipeline.append({"$limit": self.query.high_mark - self.query.low_mark})
        return self.collection.aggregate(pipeline)


def where_node(self, compiler, connection):
    if self.connector == AND:
        full_needed, empty_needed = len(self.children), 1
    else:
        full_needed, empty_needed = 1, len(self.children)

    if self.connector == AND:
        operator = "$and"
    elif self.connector == XOR:
        # https://github.com/mongodb-labs/django-mongodb/issues/27
        raise NotImplementedError("XOR is not yet supported.")
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
    WhereNode.as_mql = where_node
