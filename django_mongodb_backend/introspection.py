from django.db.backends.base.introspection import BaseDatabaseIntrospection
from django.db.models import Index
from pymongo import ASCENDING, DESCENDING


class DatabaseIntrospection(BaseDatabaseIntrospection):
    ORDER_DIR = {ASCENDING: "ASC", DESCENDING: "DESC"}

    def table_names(self, cursor=None, include_views=False):
        return sorted([x["name"] for x in self.connection.database.list_collections()])

    def get_constraints(self, cursor, table_name):
        indexes = self.connection.get_collection(table_name).index_information()
        constraints = {}
        for name, details in indexes.items():
            # Remove underscore prefix from "_id" columns in primary key index.
            if is_primary_key := name == "_id_":
                name = "id"
                details["key"] = [("id", 1)]
            constraints[name] = {
                "check": False,
                "columns": [field for field, order in details["key"]],
                "definition": None,
                "foreign_key": None,
                "index": True,
                "orders": [self.ORDER_DIR[order] for field, order in details["key"]],
                "primary_key": is_primary_key,
                "type": Index.suffix,
                "unique": details.get("unique", False),
                "options": {},
            }
        return constraints
