from importlib import import_module

from django.db import IntegrityError, models
from django.db.models.fields.related import lazy_related_operation


class EmbeddedModelField(models.Field):
    """Field that stores a model instance."""

    def __init__(self, embedded_model=None, *args, **kwargs):
        """
        `embedded_model` is the model class of the instance that will be
        stored. Like other relational fields, it may also be passed as a
        string.
        """
        self.embedded_model = embedded_model
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if path.startswith("django_mongodb.fields.embedded_model"):
            path = path.replace("django_mongodb.fields.embedded_model", "django_mongodb.fields")
        if self.embedded_model:
            kwargs["embedded_model"] = self.embedded_model
        return name, path, args, kwargs

    def get_internal_type(self):
        return "EmbeddedModelField"

    def _set_model(self, model):
        """
        Resolve embedded model class once the field knows the model it belongs
        to.

        If the model argument passed to __init__() was a string, resolve that
        string to the corresponding model class, similar to relation fields.
        However, we need to know our own model to generate a valid key
        for the embedded model class lookup and EmbeddedModelFields are
        not contributed_to_class if used in iterable fields. Thus the
        collection field sets this field's "model" attribute in its
        contribute_to_class().
        """
        self._model = model
        if model is not None and isinstance(self.embedded_model, str):

            def _resolve_lookup(_, resolved_model):
                self.embedded_model = resolved_model

            lazy_related_operation(_resolve_lookup, model, self.embedded_model)

    model = property(lambda self: self._model, _set_model)

    def stored_model(self, column_values):
        """
        Return the fixed embedded_model this field was initialized
        with (typed embedding) or tries to determine the model from
        _module / _model keys stored together with column_values
        (untyped embedding).

        Give precedence to the field's definition model, as silently using a
        differing serialized one could hide some data integrity problems.

        Note that a single untyped EmbeddedModelField may process
        instances of different models (especially when used as a type
        of a collection field).
        """
        module = column_values.pop("_module", None)
        model = column_values.pop("_model", None)
        if self.embedded_model is not None:
            return self.embedded_model
        if module is not None:
            return getattr(import_module(module), model)
        raise IntegrityError(
            "Untyped EmbeddedModelField trying to load data without serialized model class info."
        )

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def to_python(self, value):
        """
        Passes embedded model fields' values through embedded fields
        to_python methods and reinstiatates the embedded instance.

        We expect to receive a field.attname => value dict together
        with a model class from back-end database deconversion (which
        needs to know fields of the model beforehand).
        """
        # Either the model class has already been determined during
        # deconverting values from the database or we've got a dict
        # from a deserializer that may contain model class info.
        if isinstance(value, tuple):
            embedded_model, attribute_values = value
        elif isinstance(value, dict):
            embedded_model = self.stored_model(value)
            attribute_values = value
        else:
            return value
        # Create the model instance.
        instance = embedded_model(
            **{
                # Pass values through respective fields' to_python(), leaving
                # fields for which no value is specified uninitialized.
                field.attname: field.to_python(attribute_values[field.attname])
                for field in embedded_model._meta.fields
                if field.attname in attribute_values
            }
        )
        instance._state.adding = False
        return instance

    def get_db_prep_save(self, embedded_instance, connection):
        """
        Apply pre_save() and get_db_prep_save() of embedded instance
        fields and passes a field => value mapping down to database
        type conversions.

        The embedded instance will be saved as a column => value dict
        in the end (possibly augmented with info about instance's model
        for untyped embedding), but because we need to apply database
        type conversions on embedded instance fields' values and for
        these we need to know fields those values come from, we need to
        entrust the database layer with creating the dict.
        """
        if embedded_instance is None:
            return None
        # The field's value should be an instance of the model given in
        # its declaration or at least of some model.
        embedded_model = self.embedded_model or models.Model
        if not isinstance(embedded_instance, embedded_model):
            raise TypeError(
                f"Expected instance of type {embedded_model!r}, not {type(embedded_instance)!r}."
            )
        # Apply pre_save() and get_db_prep_save() of embedded instance
        # fields, create the field => value mapping to be passed to
        # storage preprocessing.
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
        if self.embedded_model is None:
            # Untyped fields must store model info alongside values.
            field_values.update(
                (
                    ("_module", embedded_instance.__class__.__module__),
                    ("_model", embedded_instance.__class__.__name__),
                )
            )
        # This instance will exist in the database soon.
        # TODO.XXX: Ensure that this doesn't cause race conditions.
        embedded_instance._state.adding = False
        return field_values

    def validate(self, value, model_instance):
        super().validate(value, model_instance)
        if self.embedded_model is None:
            return
        for field in self.embedded_model._meta.fields:
            attname = field.attname
            field.validate(getattr(value, attname), model_instance)
