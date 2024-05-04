import re
from functools import wraps

from django.core.exceptions import FullResultSet
from django.db import DatabaseError, IntegrityError, NotSupportedError
from django.db.models.lookups import UUIDTextMixin
from django.db.models.query import QuerySet
from django.db.models.sql.where import OR, SubqueryConstraint
from django.utils.tree import Node
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


def safe_regex(regex, *re_args, **re_kwargs):
    def wrapper(value):
        return re.compile(regex % re.escape(value), *re_args, **re_kwargs)

    wrapper.__name__ = "safe_regex (%r)" % regex
    return wrapper


OPERATORS_MAP = {
    "exact": lambda val: val,
    "gt": lambda val: {"$gt": val},
    "gte": lambda val: {"$gte": val},
    "lt": lambda val: {"$lt": val},
    "lte": lambda val: {"$lte": val},
    "in": lambda val: {"$in": val},
    "range": lambda val: {"$gte": val[0], "$lte": val[1]},
    "isnull": lambda val: None if val else {"$ne": None},
    # Regex matchers.
    "iexact": safe_regex("^%s$", re.IGNORECASE),
    "startswith": safe_regex("^%s"),
    "istartswith": safe_regex("^%s", re.IGNORECASE),
    "endswith": safe_regex("%s$"),
    "iendswith": safe_regex("%s$", re.IGNORECASE),
    "contains": safe_regex("%s"),
    "icontains": safe_regex("%s", re.IGNORECASE),
    "regex": lambda val: re.compile(val),
    "iregex": lambda val: re.compile(val, re.IGNORECASE),
}

NEGATED_OPERATORS_MAP = {
    "exact": lambda val: {"$ne": val},
    "gt": lambda val: {"$lte": val},
    "gte": lambda val: {"$lt": val},
    "lt": lambda val: {"$gte": val},
    "lte": lambda val: {"$gt": val},
    "in": lambda val: {"$nin": val},
    "isnull": lambda val: {"$ne": None} if val else None,
}


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
        self.collection = self.compiler.get_collection()
        self.mongo_query = getattr(compiler.query, "raw_query", {})

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
        fields = [col.target.column for col in self.columns] if self.columns else None
        cursor = self.collection.find(self.mongo_query, fields)
        if self.ordering:
            cursor.sort(self.ordering)
        if self.query.low_mark > 0:
            cursor.skip(self.query.low_mark)
        if self.query.high_mark is not None:
            cursor.limit(int(self.query.high_mark - self.query.low_mark))
        return cursor

    def add_filters(self, filters, query=None):
        children = self._get_children(filters.children)

        if query is None:
            query = self.mongo_query

        if filters.connector == OR:
            assert "$or" not in query, "Multiple ORs are not supported."
            or_conditions = query["$or"] = []

        if filters.negated:
            self._negated = not self._negated

        for child in children:
            subquery = {} if filters.connector == OR else query

            if isinstance(child, Node):
                if filters.connector == OR and child.connector == OR and len(child.children) > 1:
                    raise DatabaseError("Nested ORs are not supported.")

                if filters.connector == OR and filters.negated:
                    raise NotImplementedError("Negated ORs are not supported.")

                self.add_filters(child, query=subquery)

                if filters.connector == OR and subquery:
                    or_conditions.extend(subquery.pop("$or", []))
                    if subquery:
                        or_conditions.append(subquery)

                continue

            try:
                field, lookup_type, value = self._decode_child(child)
            except FullResultSet:
                continue

            column = field.column
            existing = subquery.get(column)

            if self._negated and lookup_type in NEGATED_OPERATORS_MAP:
                op_func = NEGATED_OPERATORS_MAP[lookup_type]
                already_negated = True
            else:
                op_func = OPERATORS_MAP[lookup_type]
                if self._negated:
                    already_negated = False

            lookup = op_func(value)

            if existing is None:
                if self._negated and not already_negated:
                    lookup = {"$not": lookup}
                subquery[column] = lookup
                if filters.connector == OR and subquery:
                    or_conditions.append(subquery)
                continue

            if not isinstance(existing, dict):
                if not self._negated:
                    # {'a': o1} + {'a': o2} --> {'a': {'$all': [o1, o2]}}
                    assert not isinstance(lookup, dict)
                    subquery[column] = {"$all": [existing, lookup]}
                else:
                    # {'a': o1} + {'a': {'$not': o2}} --> {'a': {'$all': [o1], '$nin': [o2]}}
                    if already_negated:
                        assert list(lookup) == ["$ne"]
                        lookup = lookup["$ne"]
                    assert not isinstance(lookup, dict)
                    subquery[column] = {"$all": [existing], "$nin": [lookup]}
            else:
                not_ = existing.pop("$not", None)
                if not_:
                    assert not existing
                    if isinstance(lookup, dict):
                        assert list(lookup) == ["$ne"]
                        lookup = next(iter(lookup.values()))
                    assert not isinstance(lookup, dict), (not_, lookup)
                    if self._negated:
                        # {'not': {'a': o1}} + {'a': {'not': o2}} --> {'a': {'nin': [o1, o2]}}
                        subquery[column] = {"$nin": [not_, lookup]}
                    else:
                        # {'not': {'a': o1}} + {'a': o2} -->
                        #     {'a': {'nin': [o1], 'all': [o2]}}
                        subquery[column] = {"$nin": [not_], "$all": [lookup]}
                else:
                    if isinstance(lookup, dict):
                        if "$ne" in lookup:
                            if "$nin" in existing:
                                # {'$nin': [o1, o2]} + {'$ne': o3} --> {'$nin': [o1, o2, o3]}
                                assert "$ne" not in existing
                                existing["$nin"].append(lookup["$ne"])
                            elif "$ne" in existing:
                                # {'$ne': o1} + {'$ne': o2} --> {'$nin': [o1, o2]}
                                existing["$nin"] = [existing.pop("$ne"), lookup["$ne"]]
                            else:
                                existing.update(lookup)
                        else:
                            if "$in" in lookup and "$in" in existing:
                                # {'$in': o1} + {'$in': o2} --> {'$in': o1 union o2}
                                existing["$in"] = list(set(lookup["$in"] + existing["$in"]))
                            else:
                                # {'$gt': o1} + {'$lt': o2} --> {'$gt': o1, '$lt': o2}
                                assert all(key not in existing for key in lookup), [
                                    lookup,
                                    existing,
                                ]
                                existing.update(lookup)
                    else:
                        key = "$nin" if self._negated else "$all"
                        existing.setdefault(key, []).append(lookup)

                if filters.connector == OR and subquery:
                    or_conditions.append(subquery)

        if filters.negated:
            self._negated = not self._negated

    def _decode_child(self, child):
        """
        Produce arguments suitable for add_filter from a WHERE tree leaf
        (a tuple).
        """
        if isinstance(child, UUIDTextMixin):
            raise NotSupportedError("Pattern lookups on UUIDField are not supported.")

        rhs, rhs_params = child.process_rhs(self.compiler, self.connection)
        lookup_type = child.lookup_name
        value = rhs_params
        packed = child.lhs.get_group_by_cols()[0]
        alias = packed.alias
        column = packed.target.column
        field = child.lhs.output_field
        opts = self.query.model._meta
        if alias and alias != opts.db_table:
            raise NotSupportedError("MongoDB doesn't support JOINs and multi-table inheritance.")

        # For parent.child_set queries the field held by the constraint
        # is the parent's primary key, while the field the filter
        # should consider is the child's foreign key field.
        if column != field.column:
            if not field.primary_key:
                raise NotSupportedError(
                    "MongoDB doesn't support filtering on non-primary key ForeignKey fields."
                )

            field = next(f for f in opts.fields if f.column == column)

        value = self._normalize_lookup_value(lookup_type, value, field)

        return field, lookup_type, value

    def _normalize_lookup_value(self, lookup_type, value, field):
        """
        Undo preparations done by lookups not suitable for MongoDB, and pass
        the lookup argument through DatabaseOperations.prep_lookup_value().
        """
        # Undo Lookup.get_db_prep_lookup() putting params in a list.
        if lookup_type not in ("in", "range"):
            if len(value) > 1:
                raise DatabaseError(
                    "Filter lookup type was %s; expected the filter argument "
                    "not to be a list. Only 'in'-filters can be used with "
                    "lists." % lookup_type
                )
            value = value[0]

        # Remove percent signs added by PatternLookup.process_rhs() for LIKE
        # queries.
        if lookup_type in ("startswith", "istartswith"):
            value = value[:-1]
        elif lookup_type in ("endswith", "iendswith"):
            value = value[1:]
        elif lookup_type in ("contains", "icontains"):
            value = value[1:-1]

        return self.ops.prep_lookup_value(value, field, lookup_type)

    def _get_children(self, children):
        """
        Filter out nodes of the given constraint tree not needed for
        MongoDB queries. Check that the given constraints are supported.
        """
        result = []
        for child in children:
            if isinstance(child, SubqueryConstraint):
                raise NotSupportedError("Subqueries are not supported.")

            if isinstance(child, tuple):
                constraint, lookup_type, _, value = child

                # When doing a lookup using a QuerySet Django would use
                # a subquery, but this won't work for MongoDB.
                # TODO: Add a supports_subqueries feature and let Django
                #       evaluate subqueries instead of passing them as SQL
                #       strings (QueryWrappers) to filtering.
                if isinstance(value, QuerySet):
                    raise NotSupportedError("Subqueries are not supported.")

                # Remove leafs that were automatically added by
                # sql.Query.add_filter() to handle negations of outer joins.
                if lookup_type == "isnull" and constraint.field is None:
                    continue

            result.append(child)
        return result
