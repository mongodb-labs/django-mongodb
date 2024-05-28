from django.db.models.expressions import Col


def col(self, compiler, connection):  # noqa: ARG001
    return f"${self.target.column}"


def register_expressions():
    Col.as_mql = col
