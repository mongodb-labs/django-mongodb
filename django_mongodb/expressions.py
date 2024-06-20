from django.db.models.expressions import (
    Col,
    CombinedExpression,
    ExpressionWrapper,
    NegatedExpression,
    Value,
)


def col(self, compiler, connection):  # noqa: ARG001
    return f"${self.target.column}"


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


def value(self, compiler, connection):  # noqa: ARG001
    return {"$literal": self.value}


def register_expressions():
    Col.as_mql = col
    CombinedExpression.as_mql = combined_expression
    ExpressionWrapper.as_mql = expression_wrapper
    NegatedExpression.as_mql = negated_expression
    Value.as_mql = value
