from django.db.models import Index
from django.db.models.sql.query import Query


def _get_condition_mql(self, model, schema_editor):
    """Analogous to Index._get_condition_sql()."""
    query = Query(model=model, alias_cols=False)
    where = query.build_where(self.condition)
    compiler = query.get_compiler(connection=schema_editor.connection)
    mql_ = where.as_mql(compiler, schema_editor.connection)
    # Transform aggregate() query syntax into find() syntax.
    mql = {}
    for key in mql_:
        col, value = mql_[key]
        # multiple conditions don't work yet
        if isinstance(col, dict):
            return {}
        mql[col.lstrip("$")] = {key: value}
    return mql


def register_indexes():
    Index._get_condition_mql = _get_condition_mql
