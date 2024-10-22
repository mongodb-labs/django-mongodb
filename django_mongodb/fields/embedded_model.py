from importlib import import_module

from django.core.exceptions import ValidationError
from django.db import IntegrityError, models
from django.db.models.fields.related import lazy_related_operation


class RawField(models.Field):
    """
    Generic field to store anything your database backend allows you
    to. No validation or conversions are done for this field.
    """

    def get_internal_type(self):
        """
        Returns this field's kind. Nonrel fields are meant to extend
        the set of standard fields, so fields subclassing them should
        get the same internal type, rather than their own class name.
        """
        return "RawField"


class _FakeModel:
    """
    An object of this class can pass itself off as a model instance
    when used as an arguments to Field.pre_save method (item_fields
    of iterable fields are not actually fields of any model).
    """

    def __init__(self, field, value):
        setattr(self, field.attname, value)


EMPTY_ITER = ()


class AbstractIterableField(models.Field):
    """
    Abstract field for fields for storing iterable data type like
    ``list``, ``set`` and ``dict``.

    You can pass an instance of a field as the first argument.
    If you do, the iterable items will be piped through the passed
    field's validation and conversion routines, converting the items
    to the appropriate data type.
    """

    def __init__(self, item_field=None, *args, **kwargs):
        default = kwargs.get("default", None if kwargs.get("null") else EMPTY_ITER)

        # Ensure a new object is created every time the default is accessed.
        if default is not None and not callable(default):
            kwargs["default"] = lambda: self._type(default)

        super().__init__(*args, **kwargs)

        # Either use the provided item_field or a RawField.
        if item_field is None:
            item_field = RawField()
        elif callable(item_field):
            item_field = item_field()
        self.item_field = item_field

        # Pretend that item_field is a field of a model with just one "value"
        # field.
        assert not hasattr(self.item_field, "attname")
        self.item_field.set_attributes_from_name("value")

    def contribute_to_class(self, cls, name):
        self.item_field.model = cls
        self.item_field.name = name
        super().contribute_to_class(cls, name)

        if isinstance(self.item_field, models.ForeignKey) and isinstance(
            self.item_field.remote_field.model, str
        ):
            """
            If remote_field.model is a string because the actual class is not
            yet defined, look up the actual class later. Reference:
            django.models.fields.related.RelatedField.contribute_to_class().
            """

            def _resolve_lookup(model, related):
                self.item_field.remote_field.model = related
                self.item_field.do_related_class(related, model)

            lazy_related_operation(_resolve_lookup, cls, self.item_field.remote_field.model)

    def _map(self, function, iterable, *args, **kwargs):
        """
        Applies the function to items of the iterable and returns
        an iterable of the proper type for the field.

        Overridden by DictField to only apply the function to values.
        """
        return self._type(function(element, *args, **kwargs) for element in iterable)

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def to_python(self, value):
        """Pass value items through item_field's to_python()."""
        if value is None:
            return None
        return self._map(self.item_field.to_python, value)

    def pre_save(self, model_instance, add):
        """
        Get the value from the model_instance and passes its items
        through item_field's pre_save (using a fake model instance).
        """
        value = getattr(model_instance, self.attname)
        if value is None:
            return None
        return self._map(
            lambda item: self.item_field.pre_save(_FakeModel(self.item_field, item), add),
            value,
        )

    def get_db_prep_save(self, value, connection):
        """Apply get_db_prep_save() of item_field on value items."""
        if value is None:
            return None
        return self._map(self.item_field.get_db_prep_save, value, connection=connection)

    def get_db_prep_lookup(self, lookup_type, value, connection, prepared=False):
        """Pass the value through get_db_prep_lookup of item_field."""
        return self.item_field.get_db_prep_lookup(
            lookup_type, value, connection=connection, prepared=prepared
        )

    def validate(self, values, model_instance):
        try:
            iter(values)
        except TypeError:
            raise ValidationError("Value of type %r is not iterable." % type(values)) from None

    def formfield(self, **kwargs):
        raise NotImplementedError("No form field implemented for %r." % type(self))


class ListField(AbstractIterableField):
    """
    Field representing a Python ``list``.

    If the optional keyword argument `ordering` is given, it must be a
    callable that is passed to :meth:`list.sort` as `key` argument. If
    `ordering` is given, the items in the list will be sorted before
    sending them to the database.
    """

    _type = list

    def __init__(self, *args, **kwargs):
        self.ordering = kwargs.pop("ordering", None)
        if self.ordering is not None and not callable(self.ordering):
            raise TypeError(
                "'ordering' has to be a callable or None, " "not of type %r." % type(self.ordering)
            )
        super().__init__(*args, **kwargs)

    def get_internal_type(self):
        return "ListField"

    def pre_save(self, model_instance, add):
        value = getattr(model_instance, self.attname)
        if value is None:
            return None
        if value and self.ordering:
            value.sort(key=self.ordering)
        return super().pre_save(model_instance, add)


class EmbeddedModelField(models.Field):
    """
    Field that allows you to embed a model instance.

    :param embedded_model: (optional) The model class of instances we
                           will be embedding; may also be passed as a
                           string, similar to relation fields

    TODO: Make sure to delegate all signals and other field methods to
          the embedded instance (not just pre_save, get_db_prep_* and
          to_python).
    """

    def __init__(self, embedded_model=None, *args, **kwargs):
        self.embedded_model = embedded_model
        kwargs.setdefault("default", None)
        super().__init__(*args, **kwargs)

    def get_internal_type(self):
        return "EmbeddedModelField"

    def _set_model(self, model):
        """
        Resolves embedded model class once the field knows the model it
        belongs to.

        If the model argument passed to __init__ was a string, we need
        to make sure to resolve that string to the corresponding model
        class, similar to relation fields.
        However, we need to know our own model to generate a valid key
        for the embedded model class lookup and EmbeddedModelFields are
        not contributed_to_class if used in iterable fields. Thus we
        rely on the collection field telling us its model (by setting
        our "model" attribute in its contribute_to_class method).
        """
        self._model = model
        if model is not None and isinstance(self.embedded_model, str):

            def _resolve_lookup(_, resolved_model):
                self.embedded_model = resolved_model

            lazy_related_operation(_resolve_lookup, model, self.embedded_model)

    model = property(lambda self: self._model, _set_model)

    def stored_model(self, column_values):
        """
        Returns the fixed embedded_model this field was initialized
        with (typed embedding) or tries to determine the model from
        _module / _model keys stored together with column_values
        (untyped embedding).

        We give precedence to the field's definition model, as silently
        using a differing serialized one could hide some data integrity
        problems.

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
        # Pass values through respective fields' to_python, leaving
        # fields for which no value is specified uninitialized.
        attribute_values = {
            field.attname: field.to_python(attribute_values[field.attname])
            for field in embedded_model._meta.fields
            if field.attname in attribute_values
        }
        # Create the model instance.
        instance = embedded_model(**attribute_values)
        instance._state.adding = False
        return instance

    def get_db_prep_save(self, embedded_instance, connection):
        """
        Applies pre_save and get_db_prep_save of embedded instance
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
        # Apply pre_save and get_db_prep_save of embedded instance
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
        # Let untyped fields store model info alongside values.
        # Use fake RawFields for additional values to avoid passing
        # embedded_instance to database conversions and to give
        # backends a chance to apply generic conversions.
        if self.embedded_model is None:
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
