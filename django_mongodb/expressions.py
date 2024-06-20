from django.db.models.expressions import Col, ExpressionWrapper, Value


def col(self, compiler, connection):  # noqa: ARG001
    return f"${self.target.column}"


def expression_wrapper(self, compiler, connection):
    return self.expression.as_mql(compiler, connection)


def value(self, compiler, connection):  # noqa: ARG001
    return {"$literal": self.value}


def register_expressions():
    Col.as_mql = col
    ExpressionWrapper.as_mql = expression_wrapper
    Value.as_mql = value
