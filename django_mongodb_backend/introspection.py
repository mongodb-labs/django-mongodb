from django.db.backends.base.introspection import BaseDatabaseIntrospection
from django.db.models import Index
from pymongo import ASCENDING, DESCENDING

from django_mongodb_backend.indexes import AtlasSearchIndex, AtlasVectorSearchIndex


class DatabaseIntrospection(BaseDatabaseIntrospection):
    ORDER_DIR = {ASCENDING: "ASC", DESCENDING: "DESC"}

    def table_names(self, cursor=None, include_views=False):
        return sorted([x["name"] for x in self.connection.database.list_collections()])

    def _get_index_info(self, table_name):
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

    def _get_atlas_index_info(self, table_name):
        constraints = {}
        indexes = self.connection.get_collection(table_name).list_search_indexes()
        for details in indexes:
            if details["type"] == "vectorSearch":
                columns = [field["path"] for field in details["latestDefinition"]["fields"]]
                type_ = AtlasVectorSearchIndex.suffix
                options = details
            else:
                columns = list(details["latestDefinition"]["mappings"].get("fields", {}).keys())
                options = details["latestDefinition"]["mappings"]
                type_ = AtlasSearchIndex.suffix
            constraints[details["name"]] = {
                "check": False,
                "columns": columns,
                "definition": None,
                "foreign_key": None,
                "index": True,
                "orders": [],
                "primary_key": False,
                "type": type_,
                "unique": False,
                "options": options,
            }
        return constraints

    def get_constraints(self, cursor, table_name):
        return {**self._get_index_info(table_name), **self._get_atlas_index_info(table_name)}
