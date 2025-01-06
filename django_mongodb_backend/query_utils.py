from django.core.exceptions import FullResultSet
from django.db.models.aggregates import Aggregate
from django.db.models.expressions import Value


def is_direct_value(node):
    return not hasattr(node, "as_sql")


def process_lhs(node, compiler, connection):
    if not hasattr(node, "lhs"):
        # node is a Func or Expression, possibly with multiple source expressions.
        result = []
        for expr in node.get_source_expressions():
            try:
                result.append(expr.as_mql(compiler, connection))
            except FullResultSet:
                result.append(Value(True).as_mql(compiler, connection))
        if isinstance(node, Aggregate):
            return result[0]
        return result
    # node is a Transform with just one source expression, aliased as "lhs".
    if is_direct_value(node.lhs):
        return node
    return node.lhs.as_mql(compiler, connection)


def process_rhs(node, compiler, connection):
    rhs = node.rhs
    if hasattr(rhs, "as_mql"):
        if getattr(rhs, "subquery", False):
            value = rhs.as_mql(compiler, connection, lookup_name=node.lookup_name)
        else:
            value = rhs.as_mql(compiler, connection)
    else:
        _, value = node.process_rhs(compiler, connection)
        lookup_name = node.lookup_name
        # Undo Lookup.get_db_prep_lookup() putting params in a list.
        if lookup_name not in ("in", "range"):
            value = value[0]
    if hasattr(node, "prep_lookup_value_mongo"):
        value = node.prep_lookup_value_mongo(value)
    # No need to prepare expressions like F() objects.
    if hasattr(rhs, "resolve_expression"):
        return value
    return connection.ops.prep_lookup_value(value, node.lhs.output_field, node.lookup_name)


def regex_match(field, regex_vals, insensitive=False):
    regex = {"$concat": regex_vals} if isinstance(regex_vals, tuple) else regex_vals
    options = "i" if insensitive else ""
    return {"$regexMatch": {"input": {"$toString": field}, "regex": regex, "options": options}}
