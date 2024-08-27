from django.db.backends.base.introspection import BaseDatabaseIntrospection


class DatabaseIntrospection(BaseDatabaseIntrospection):
    def table_names(self, cursor=None, include_views=False):
        return sorted([x["name"] for x in self.connection.database.list_collections()])
