from django.db.models.sql.constants import INNER
from django.db.models.sql.datastructures import Join


def join(self, compiler, connection):
    lookups_pipeline = []
    join_fields = self.join_fields or self.join_cols
    lhs_fields = []
    rhs_fields = []
    for lhs, rhs in join_fields:
        if isinstance(lhs, str):
            lhs_mql = lhs
            rhs_mql = rhs
        else:
            lhs, rhs = connection.ops.prepare_join_on_clause(
                self.parent_alias, lhs, self.table_name, rhs
            )
            lhs_mql = lhs.as_mql(compiler, connection)
            rhs_mql = rhs.as_mql(compiler, connection)
            # replace prefix, in lookup stages the reference
            # to this column is without the collection name.
            rhs_mql = rhs_mql.replace(f"{self.table_name}.", "", 1)
        lhs_fields.append(lhs_mql)
        rhs_fields.append(rhs_mql)

    # temp_table_name = f"{self.table_alias}__array"
    parent_template = "parent__field__"
    lookups_pipeline = [
        {
            "$lookup": {
                "from": self.table_name,
                "let": {
                    f"{parent_template}{i}": parent_field
                    for i, parent_field in enumerate(lhs_fields)
                },
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    {"$eq": [f"$${parent_template}{i}", field]}
                                    for i, field in enumerate(rhs_fields)
                                ]
                            }
                        }
                    }
                ],
                "as": self.table_alias,
            }
        },
    ]
    if self.join_type != INNER:
        lookups_pipeline.append(
            {
                "$project": {
                    self.table_alias: {
                        "$cond": {
                            "if": {
                                "$or": [
                                    {"$eq": [{"$type": "$arrayField"}, "missing"]},
                                    {"$eq": [{"$size": "$arrayField"}, 0]},
                                ]
                            },
                            "then": [None],
                            "else": "$arrayField",
                        }
                    }
                }
            }
        )
    lookups_pipeline.append({"$unwind": f"${self.table_alias}"})
    return lookups_pipeline


def register_structures():
    Join.as_mql = join
