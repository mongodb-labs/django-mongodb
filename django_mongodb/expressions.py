from django.db.models.expressions import Col, Value


def col(self, compiler, connection):  # noqa: ARG001
    return f"${self.target.column}"


def value(self, compiler, connection):  # noqa: ARG001
    return {"$literal": self.value}


def register_expressions():
    Col.as_mql = col
    Value.as_mql = value
