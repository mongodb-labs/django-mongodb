from django.db import models

from django_mongodb.fields import EmbeddedModelField, ListField


def count_calls(func):
    def wrapper(*args, **kwargs):
        wrapper.calls += 1
        return func(*args, **kwargs)

    wrapper.calls = 0

    return wrapper


class ReferenceList(models.Model):
    keys = ListField(models.ForeignKey("Model", models.CASCADE))


class Model(models.Model):
    pass


class Target(models.Model):
    index = models.IntegerField()


class DecimalModel(models.Model):
    decimal = models.DecimalField(max_digits=9, decimal_places=2)


class DecimalKey(models.Model):
    decimal = models.DecimalField(max_digits=9, decimal_places=2, primary_key=True)


class DecimalParent(models.Model):
    child = models.ForeignKey(DecimalKey, models.CASCADE)


class DecimalsList(models.Model):
    decimals = ListField(models.ForeignKey(DecimalKey, models.CASCADE))


class OrderedListModel(models.Model):
    ordered_ints = ListField(
        models.IntegerField(max_length=500),
        default=[],
        ordering=count_calls(lambda x: x),
        null=True,
    )
    ordered_nullable = ListField(ordering=lambda x: x, null=True)


class ListModel(models.Model):
    integer = models.IntegerField(primary_key=True)
    floating_point = models.FloatField()
    names = ListField(models.CharField)
    names_with_default = ListField(models.CharField(max_length=500), default=[])
    names_nullable = ListField(models.CharField(max_length=500), null=True)


class EmbeddedModelFieldModel(models.Model):
    simple = EmbeddedModelField("EmbeddedModel", null=True)
    simple_untyped = EmbeddedModelField(null=True)
    decimal_parent = EmbeddedModelField(DecimalParent, null=True)
    #    typed_list = ListField(EmbeddedModelField('SetModel'))
    typed_list2 = ListField(EmbeddedModelField("EmbeddedModel"))
    untyped_list = ListField(EmbeddedModelField())
    #    untyped_dict = DictField(EmbeddedModelField())
    ordered_list = ListField(EmbeddedModelField(), ordering=lambda obj: obj.index)


class EmbeddedModel(models.Model):
    some_relation = models.ForeignKey(Target, models.CASCADE, null=True)
    someint = models.IntegerField(db_column="custom")
    auto_now = models.DateTimeField(auto_now=True)
    auto_now_add = models.DateTimeField(auto_now_add=True)


class Child(models.Model):
    pass


class Parent(models.Model):
    id = models.IntegerField(primary_key=True)
    integer_list = ListField(models.IntegerField)

    #    integer_dict = DictField(models.IntegerField)
    embedded_list = ListField(EmbeddedModelField(Child))


#    embedded_dict = DictField(EmbeddedModelField(Child))
