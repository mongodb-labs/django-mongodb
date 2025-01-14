from django.core import checks
from django.db import models
from django.db.models.fields.related import lazy_related_operation
from django.db.models.lookups import Transform

from .. import forms


class EmbeddedModelField(models.Field):
    """Field that stores a model instance."""

    def __init__(self, embedded_model, *args, **kwargs):
        """
        `embedded_model` is the model class of the instance to be stored.
        Like other relational fields, it may also be passed as a string.
        """
        self.embedded_model = embedded_model
        super().__init__(*args, **kwargs)

    def check(self, **kwargs):
        errors = super().check(**kwargs)
        for field in self.embedded_model._meta.fields:
            if field.remote_field:
                errors.append(
                    checks.Error(
                        "Embedded models cannot have relational fields "
                        f"({self.embedded_model().__class__.__name__}.{field.name} "
                        f"is a {field.__class__.__name__}).",
                        obj=self,
                        id="django_mongodb.embedded_model.E001",
                    )
                )
        return errors

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if path.startswith("django_mongodb_backend.fields.embedded_model"):
            path = path.replace(
                "django_mongodb_backend.fields.embedded_model", "django_mongodb_backend.fields"
            )
        kwargs["embedded_model"] = self.embedded_model
        return name, path, args, kwargs

    def get_internal_type(self):
        return "EmbeddedModelField"

    def _set_model(self, model):
        """
        Resolve embedded model class once the field knows the model it belongs
        to. If __init__()'s embedded_model argument is a string, resolve it to
        the actual model class, similar to relation fields.
        """
        self._model = model
        if model is not None and isinstance(self.embedded_model, str):

            def _resolve_lookup(_, resolved_model):
                self.embedded_model = resolved_model

            lazy_related_operation(_resolve_lookup, model, self.embedded_model)

    model = property(lambda self: self._model, _set_model)

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def to_python(self, value):
        """
        Pass embedded model fields' values through each field's to_python() and
        reinstantiate the embedded instance.
        """
        if value is None:
            return None
        if not isinstance(value, dict):
            return value
        instance = self.embedded_model(
            **{
                field.attname: field.to_python(value[field.attname])
                for field in self.embedded_model._meta.fields
                if field.attname in value
            }
        )
        instance._state.adding = False
        return instance

    def get_db_prep_save(self, embedded_instance, connection):
        """
        Apply pre_save() and get_db_prep_save() of embedded instance fields and
        create the {field: value} dict to be saved.
        """
        if embedded_instance is None:
            return None
        if not isinstance(embedded_instance, self.embedded_model):
            raise TypeError(
                f"Expected instance of type {self.embedded_model!r}, not "
                f"{type(embedded_instance)!r}."
            )
        field_values = {}
        add = embedded_instance._state.adding
        for field in embedded_instance._meta.fields:
            value = field.get_db_prep_save(
                field.pre_save(embedded_instance, add), connection=connection
            )
            # Exclude unset primary keys (e.g. {'id': None}).
            if field.primary_key and value is None:
                continue
            field_values[field.attname] = value
        # This instance will exist in the database soon.
        embedded_instance._state.adding = False
        return field_values

    def get_transform(self, name):
        transform = super().get_transform(name)
        if transform:
            return transform
        return KeyTransformFactory(name)

    def validate(self, value, model_instance):
        super().validate(value, model_instance)
        if self.embedded_model is None:
            return
        for field in self.embedded_model._meta.fields:
            attname = field.attname
            field.validate(getattr(value, attname), model_instance)

    def formfield(self, **kwargs):
        return super().formfield(
            **{
                "form_class": forms.EmbeddedModelField,
                "model": self.embedded_model,
                "prefix": self.name,
                **kwargs,
            }
        )


class KeyTransform(Transform):
    def __init__(self, key_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.key_name = str(key_name)

    def preprocess_lhs(self, compiler, connection):
        key_transforms = [self.key_name]
        previous = self.lhs
        while isinstance(previous, KeyTransform):
            key_transforms.insert(0, previous.key_name)
            previous = previous.lhs
        mql = previous.as_mql(compiler, connection)
        return mql, key_transforms

    def as_mql(self, compiler, connection):
        mql, key_transforms = self.preprocess_lhs(compiler, connection)
        transforms = ".".join(key_transforms)
        return f"{mql}.{transforms}"


class KeyTransformFactory:
    def __init__(self, key_name):
        self.key_name = key_name

    def __call__(self, *args, **kwargs):
        return KeyTransform(self.key_name, *args, **kwargs)
