from django.db import NotSupportedError
from django.db.models import Index
from django.db.models.lookups import BuiltinLookup
from django.db.models.sql.query import Query
from django.db.models.sql.where import AND, XOR, WhereNode

from .query_utils import process_rhs

MONGO_INDEX_OPERATORS = {
    "exact": "$eq",
    "gt": "$gt",
    "gte": "$gte",
    "lt": "$lt",
    "lte": "$lte",
    "in": "$in",
}


def _get_condition_mql(self, model, schema_editor):
    """Analogous to Index._get_condition_sql()."""
    query = Query(model=model, alias_cols=False)
    where = query.build_where(self.condition)
    compiler = query.get_compiler(connection=schema_editor.connection)
    return where.as_mql_idx(compiler, schema_editor.connection)


def builtin_lookup_idx(self, compiler, connection):
    lhs_mql = self.lhs.target.column
    value = process_rhs(self, compiler, connection)
    try:
        operator = MONGO_INDEX_OPERATORS[self.lookup_name]
    except KeyError:
        raise NotSupportedError(
            f"MongoDB does not support the '{self.lookup_name}' lookup in indexes."
        ) from None
    return {lhs_mql: {operator: value}}


def where_node_idx(self, compiler, connection):
    if self.connector == AND:
        operator = "$and"
    elif self.connector == XOR:
        raise NotSupportedError("MongoDB does not support the '^' operator lookup in indexes.")
    else:
        operator = "$or"
    if self.negated:
        raise NotSupportedError("MongoDB does not support the '~' operator in indexes.")
    children_mql = []
    for child in self.children:
        mql = child.as_mql_idx(compiler, connection)
        children_mql.append(mql)
    if len(children_mql) == 1:
        mql = children_mql[0]
    elif len(children_mql) > 1:
        mql = {operator: children_mql}
    else:
        mql = {}
    return mql


def register_indexes():
    BuiltinLookup.as_mql_idx = builtin_lookup_idx
    Index._get_condition_mql = _get_condition_mql
    WhereNode.as_mql_idx = where_node_idx
