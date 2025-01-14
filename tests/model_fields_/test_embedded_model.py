from django.core.exceptions import ValidationError
from django.db import models
from django.test import SimpleTestCase, TestCase
from django.test.utils import isolate_apps

from django_mongodb_backend.fields import EmbeddedModelField

from .models import (
    Address,
    Author,
    Book,
    Data,
    Holder,
)


class MethodTests(SimpleTestCase):
    def test_deconstruct(self):
        field = EmbeddedModelField("Data", null=True)
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django_mongodb_backend.fields.EmbeddedModelField")
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"embedded_model": "Data", "null": True})

    def test_get_db_prep_save_invalid(self):
        msg = "Expected instance of type <class 'model_fields_.models.Data'>, " "not <class 'int'>."
        with self.assertRaisesMessage(TypeError, msg):
            Holder(data=42).save()

    def test_validate(self):
        obj = Holder(data=Data(integer=None))
        # This isn't quite right because "integer" is the subfield of data
        # that's non-null.
        msg = "{'data': ['This field cannot be null.']}"
        with self.assertRaisesMessage(ValidationError, msg):
            obj.full_clean()


class ModelTests(TestCase):
    def truncate_ms(self, value):
        """Truncate microseconds to milliseconds as supported by MongoDB."""
        return value.replace(microsecond=(value.microsecond // 1000) * 1000)

    def test_save_load(self):
        Holder.objects.create(data=Data(integer="5"))
        obj = Holder.objects.get()
        self.assertIsInstance(obj.data, Data)
        # get_prep_value() is called, transforming string to int.
        self.assertEqual(obj.data.integer, 5)
        # Primary keys should not be populated...
        self.assertEqual(obj.data.id, None)
        # ... unless set explicitly.
        obj.data.id = obj.id
        obj.save()
        obj = Holder.objects.get()
        self.assertEqual(obj.data.id, obj.id)

    def test_save_load_null(self):
        Holder.objects.create(data=None)
        obj = Holder.objects.get()
        self.assertIsNone(obj.data)

    def test_pre_save(self):
        """Field.pre_save() is called on embedded model fields."""
        obj = Holder.objects.create(data=Data())
        auto_now = self.truncate_ms(obj.data.auto_now)
        auto_now_add = self.truncate_ms(obj.data.auto_now_add)
        self.assertEqual(auto_now, auto_now_add)
        # save() updates auto_now but not auto_now_add.
        obj.save()
        self.assertEqual(self.truncate_ms(obj.data.auto_now_add), auto_now_add)
        auto_now_two = obj.data.auto_now
        self.assertGreater(auto_now_two, obj.data.auto_now_add)
        # And again, save() updates auto_now but not auto_now_add.
        obj = Holder.objects.get()
        obj.save()
        self.assertEqual(obj.data.auto_now_add, auto_now_add)
        self.assertGreater(obj.data.auto_now, auto_now_two)


class QueryingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.objs = [Holder.objects.create(data=Data(integer=x)) for x in range(6)]

    def test_exact(self):
        self.assertCountEqual(Holder.objects.filter(data__integer=3), [self.objs[3]])

    def test_lt(self):
        self.assertCountEqual(Holder.objects.filter(data__integer__lt=3), self.objs[:3])

    def test_lte(self):
        self.assertCountEqual(Holder.objects.filter(data__integer__lte=3), self.objs[:4])

    def test_gt(self):
        self.assertCountEqual(Holder.objects.filter(data__integer__gt=3), self.objs[4:])

    def test_gte(self):
        self.assertCountEqual(Holder.objects.filter(data__integer__gte=3), self.objs[3:])

    def test_nested(self):
        obj = Book.objects.create(
            author=Author(name="Shakespeare", age=55, address=Address(city="NYC", state="NY"))
        )
        self.assertCountEqual(Book.objects.filter(author__address__city="NYC"), [obj])


@isolate_apps("model_fields_")
class CheckTests(SimpleTestCase):
    def test_no_relational_fields(self):
        class Target(models.Model):
            key = models.ForeignKey("MyModel", models.CASCADE)

        class MyModel(models.Model):
            field = EmbeddedModelField(Target)

        model = MyModel()
        errors = model.check()
        self.assertEqual(len(errors), 1)
        # The inner CharField has a non-positive max_length.
        self.assertEqual(errors[0].id, "django_mongodb.embedded_model.E001")
        msg = errors[0].msg
        self.assertEqual(
            msg, "Embedded models cannot have relational fields (Target.key is a ForeignKey)."
        )
