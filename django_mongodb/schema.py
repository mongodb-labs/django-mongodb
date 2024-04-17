from django.db.backends.base.schema import BaseDatabaseSchemaEditor


class DatabaseSchemaEditor(BaseDatabaseSchemaEditor):
    def create_model(self, model):
        pass

    def add_field(self, model, field):
        pass

    def alter_field(self, model, old_field, new_field, strict=False):
        pass

    def remove_field(self, model, field):
        pass

    def alter_unique_together(self, model, old_unique_together, new_unique_together):
        pass

    def add_index(self, model, index):
        pass

    def remove_index(self, model, index):
        pass
