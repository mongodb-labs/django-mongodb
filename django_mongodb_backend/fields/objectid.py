from bson import ObjectId, errors
from django.core import exceptions
from django.db.models.fields import Field
from django.utils.translation import gettext_lazy as _

from django_mongodb_backend import forms


class ObjectIdMixin:
    default_error_messages = {
        "invalid": _("“%(value)s” is not a valid Object Id."),
    }
    description = _("Object Id")

    def db_type(self, connection):
        return "objectId"

    def rel_db_type(self, connection):
        return "objectId"

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        return self.to_python(value)

    def to_python(self, value):
        if value is None:
            return value
        try:
            return ObjectId(value)
        except (errors.InvalidId, TypeError):
            raise exceptions.ValidationError(
                self.error_messages["invalid"],
                code="invalid",
                params={"value": value},
            ) from None

    def formfield(self, **kwargs):
        return super().formfield(
            **{
                "form_class": forms.ObjectIdField,
                **kwargs,
            }
        )


class ObjectIdField(ObjectIdMixin, Field):
    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if path.startswith("django_mongodb_backend.fields.objectid"):
            path = path.replace(
                "django_mongodb_backend.fields.objectid",
                "django_mongodb_backend.fields",
            )
        return name, path, args, kwargs

    def get_internal_type(self):
        return "ObjectIdField"
