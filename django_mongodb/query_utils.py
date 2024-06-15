import re

from django.core.exceptions import FullResultSet
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
        return result
    # node is a Transform with just one source expression, aliased as "lhs".
    if is_direct_value(node.lhs):
        return node
    return node.lhs.as_mql(compiler, connection)


def process_rhs(node, compiler, connection):
    rhs = node.rhs
    if hasattr(rhs, "as_mql"):
        return rhs.as_mql(compiler, connection)
    _, value = node.process_rhs(compiler, connection)
    lookup_name = node.lookup_name
    # Undo Lookup.get_db_prep_lookup() putting params in a list.
    if lookup_name not in ("in", "range"):
        value = value[0]
    # Remove percent signs added by PatternLookup.process_rhs() for LIKE
    # queries.
    if lookup_name in ("startswith", "istartswith"):
        value = value[:-1]
    elif lookup_name in ("endswith", "iendswith"):
        value = value[1:]
    elif lookup_name in ("contains", "icontains"):
        value = value[1:-1]

    return connection.ops.prep_lookup_value(value, node.lhs.output_field, node.lookup_name)


def regex_match(field, value, regex, *re_args, **re_kwargs):
    regex = re.compile(regex % re.escape(value), *re_args, **re_kwargs)
    options = "i" if regex.flags & re.I else ""
    return {"$regexMatch": {"input": field, "regex": regex.pattern, "options": options}}
