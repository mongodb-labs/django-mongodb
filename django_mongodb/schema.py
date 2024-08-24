from django.db.backends.base.schema import BaseDatabaseSchemaEditor


class DatabaseSchemaEditor(BaseDatabaseSchemaEditor):
    def create_model(self, model):
        self.connection.database.create_collection(model._meta.db_table)

    def delete_model(self, model):
        self.connection.database[model._meta.db_table].drop()

    def add_field(self, model, field):
        pass

    def alter_field(self, model, old_field, new_field, strict=False):
        pass

    def remove_field(self, model, field):
        pass

    def alter_index_together(self, model, old_index_together, new_index_together):
        pass

    def alter_unique_together(self, model, old_unique_together, new_unique_together):
        pass

    def add_index(self, model, index):
        pass

    def rename_index(self, model, old_index, new_index):
        pass

    def remove_index(self, model, index):
        pass

    def add_constraint(self, model, constraint):
        pass

    def remove_constraint(self, model, constraint):
        pass

    def alter_db_table(self, model, old_db_table, new_db_table):
        pass
