import enum

from django.db import models

from django_mongodb_backend.fields import ArrayField, ObjectIdField


class ObjectIdModel(models.Model):
    field = ObjectIdField()


class NullableObjectIdModel(models.Model):
    field = ObjectIdField(blank=True, null=True)


class PrimaryKeyObjectIdModel(models.Model):
    field = ObjectIdField(primary_key=True)


class ArrayFieldSubclass(ArrayField):
    def __init__(self, *args, **kwargs):
        super().__init__(models.IntegerField())


class Tag:
    def __init__(self, tag_id):
        self.tag_id = tag_id

    def __eq__(self, other):
        return isinstance(other, Tag) and self.tag_id == other.tag_id


class TagField(models.SmallIntegerField):
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return Tag(int(value))

    def to_python(self, value):
        if isinstance(value, Tag):
            return value
        if value is None:
            return value
        return Tag(int(value))

    def get_prep_value(self, value):
        return value.tag_id


class IntegerArrayModel(models.Model):
    field = ArrayField(models.IntegerField(), default=list, blank=True)


class NullableIntegerArrayModel(models.Model):
    field = ArrayField(models.IntegerField(), blank=True, null=True)
    field_nested = ArrayField(ArrayField(models.IntegerField(null=True)), null=True)
    order = models.IntegerField(null=True)

    def __str__(self):
        return str(self.field)


class CharArrayModel(models.Model):
    field = ArrayField(models.CharField(max_length=10))


class DateTimeArrayModel(models.Model):
    datetimes = ArrayField(models.DateTimeField())
    dates = ArrayField(models.DateField())
    times = ArrayField(models.TimeField())


class NestedIntegerArrayModel(models.Model):
    field = ArrayField(ArrayField(models.IntegerField()))


class OtherTypesArrayModel(models.Model):
    ips = ArrayField(models.GenericIPAddressField(), default=list)
    uuids = ArrayField(models.UUIDField(), default=list)
    decimals = ArrayField(models.DecimalField(max_digits=5, decimal_places=2), default=list)
    tags = ArrayField(TagField(), blank=True, null=True)
    json = ArrayField(models.JSONField(default=dict), default=list)


class EnumField(models.CharField):
    def get_prep_value(self, value):
        return value.value if isinstance(value, enum.Enum) else value


class ArrayEnumModel(models.Model):
    array_of_enums = ArrayField(EnumField(max_length=20))
