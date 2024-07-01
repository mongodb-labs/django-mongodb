import datetime
from decimal import Decimal

from bson import Decimal128
from django.core.exceptions import EmptyResultSet, FullResultSet
from django.db.models.expressions import (
    Case,
    Col,
    CombinedExpression,
    ExpressionWrapper,
    NegatedExpression,
    Value,
    When,
)


def case(self, compiler, connection):
    case_parts = []
    for case in self.cases:
        case_mql = {}
        try:
            case_mql["case"] = case.as_mql(compiler, connection)
        except EmptyResultSet:
            continue
        except FullResultSet:
            default_mql = case.result.as_mql(compiler, connection)
            break
        case_mql["then"] = case.result.as_mql(compiler, connection)
        case_parts.append(case_mql)
    else:
        default_mql = self.default.as_mql(compiler, connection)
    if not case_parts:
        return default_mql
    return {
        "$switch": {
            "branches": case_parts,
            "default": default_mql,
        }
    }


def col(self, compiler, connection):  # noqa: ARG001
    prefix = f"{self.alias}." if self.alias != compiler.collection_name else ""
    return f"${prefix}{self.target.column}"


def combined_expression(self, compiler, connection):
    expressions = [
        self.lhs.as_mql(compiler, connection),
        self.rhs.as_mql(compiler, connection),
    ]
    return connection.ops.combine_expression(self.connector, expressions)


def expression_wrapper(self, compiler, connection):
    return self.expression.as_mql(compiler, connection)


def negated_expression(self, compiler, connection):
    return {"$not": expression_wrapper(self, compiler, connection)}


def when(self, compiler, connection):
    return self.condition.as_mql(compiler, connection)


def value(self, compiler, connection):  # noqa: ARG001
    value = self.value
    if isinstance(value, Decimal):
        value = Decimal128(value)
    elif isinstance(value, datetime.date):
        # Turn dates into datetimes since BSON doesn't support dates.
        value = datetime.datetime.combine(value, datetime.datetime.min.time())
    return {"$literal": value}


def register_expressions():
    Case.as_mql = case
    Col.as_mql = col
    CombinedExpression.as_mql = combined_expression
    ExpressionWrapper.as_mql = expression_wrapper
    NegatedExpression.as_mql = negated_expression
    When.as_mql = when
    Value.as_mql = value
