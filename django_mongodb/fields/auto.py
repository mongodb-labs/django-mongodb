from bson import ObjectId, errors
from django.core import exceptions
from django.db.models.fields import AutoField
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _


class ObjectIdAutoField(AutoField):
    default_error_messages = {
        "invalid": _("“%(value)s” value must be an Object Id."),
    }
    description = _("Object Id")

    def __init__(self, *args, **kwargs):
        kwargs["db_column"] = "_id"
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.db_column == "_id":
            del kwargs["db_column"]
        if path.startswith("django_mongodb.fields.auto"):
            path = path.replace("django_mongodb.fields.auto", "django_mongodb.fields")
        return name, path, args, kwargs

    def get_prep_value(self, value):
        if value is None:
            return None
        # Accept int for compatibility with Django's test suite which has many
        # instances of manually assigned integer IDs, as well as for things
        # like settings.SITE_ID which has a system check requiring an integer.
        if isinstance(value, (ObjectId | int)):
            return value
        try:
            return ObjectId(value)
        except errors.InvalidId as e:
            # A manually assigned integer ID?
            if isinstance(value, str) and value.isdigit():
                return int(value)
            raise ValueError(f"Field '{self.name}' expected an ObjectId but got {value!r}.") from e

    def db_type(self, connection):
        return "objectId"

    def rel_db_type(self, connection):
        return "objectId"

    def to_python(self, value):
        if value is None or isinstance(value, int):
            return value
        try:
            return ObjectId(value)
        except errors.InvalidId:
            try:
                return int(value)
            except ValueError:
                raise exceptions.ValidationError(
                    self.error_messages["invalid"],
                    code="invalid",
                    params={"value": value},
                ) from None

    @cached_property
    def validators(self):
        # Avoid IntegerField validators inherited from AutoField.
        return [*self.default_validators, *self._validators]
