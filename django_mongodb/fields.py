from bson import ObjectId, errors
from django.core import exceptions
from django.db.models.fields import AutoField, Field
from django.utils.translation import gettext_lazy as _


class MongoAutoField(AutoField):
    default_error_messages = {
        "invalid": _("“%(value)s” value must be an Object Id."),
    }
    description = _("Object Id")

    def __init__(self, *args, **kwargs):
        kwargs["db_column"] = "_id"
        super().__init__(*args, **kwargs)

    def get_prep_value(self, value):
        # Override AutoField casting to integer.
        return Field.get_prep_value(self, value)

    def rel_db_type(self, connection):
        return Field().db_type(connection=connection)

    def to_python(self, value):
        if value is None:
            return value
        try:
            return ObjectId(value)
        except errors.InvalidId:
            raise exceptions.ValidationError(
                self.error_messages["invalid"],
                code="invalid",
                params={"value": value},
            ) from None
