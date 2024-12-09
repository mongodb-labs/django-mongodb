from bson import ObjectId
from bson.errors import InvalidId
from django.core.exceptions import ValidationError
from django.forms import Field
from django.utils.translation import gettext_lazy as _


class ObjectIdField(Field):
    default_error_messages = {
        "invalid": _("Enter a valid Object Id."),
    }

    def prepare_value(self, value):
        if isinstance(value, ObjectId):
            return str(value)
        return value

    def to_python(self, value):
        value = super().to_python(value)
        if value in self.empty_values:
            return None
        if not isinstance(value, ObjectId):
            try:
                value = ObjectId(value)
            except InvalidId:
                raise ValidationError(self.error_messages["invalid"], code="invalid") from None
        return value
