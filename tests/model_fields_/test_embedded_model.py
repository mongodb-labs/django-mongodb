from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase

from django_mongodb.fields import EmbeddedModelField

from .models import (
    DecimalKey,
    DecimalParent,
    EmbeddedModel,
    EmbeddedModelFieldModel,
    Target,
)


class MethodTests(SimpleTestCase):
    def test_deconstruct(self):
        field = EmbeddedModelField("EmbeddedModel", null=True)
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django_mongodb.fields.EmbeddedModelField")
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"embedded_model": "EmbeddedModel", "null": True})

    def test_get_db_prep_save_invalid(self):
        msg = (
            "Expected instance of type <class 'model_fields_.models.EmbeddedModel'>, "
            "not <class 'int'>."
        )
        with self.assertRaisesMessage(TypeError, msg):
            EmbeddedModelFieldModel(simple=42).save()

    def test_validate(self):
        obj = EmbeddedModelFieldModel(simple=EmbeddedModel(someint=None))
        # This isn't quite right because "someint" is the field that's non-null.
        msg = "{'simple': ['This field cannot be null.']}"
        with self.assertRaisesMessage(ValidationError, msg):
            obj.full_clean()


class ModelTests(TestCase):
    def truncate_ms(self, value):
        """Truncate microsends to millisecond precision as supported by MongoDB."""
        return value.replace(microsecond=(value.microsecond // 1000) * 1000)

    def test_save_load(self):
        EmbeddedModelFieldModel.objects.create(simple=EmbeddedModel(someint="5"))
        obj = EmbeddedModelFieldModel.objects.get()
        self.assertIsInstance(obj.simple, EmbeddedModel)
        # Make sure get_prep_value is called.
        self.assertEqual(obj.simple.someint, 5)
        # Primary keys should not be populated...
        self.assertEqual(obj.simple.id, None)
        # ... unless set explicitly.
        obj.simple.id = obj.id
        obj.save()
        obj = EmbeddedModelFieldModel.objects.get()
        self.assertEqual(obj.simple.id, obj.id)

    def test_save_load_null(self):
        EmbeddedModelFieldModel.objects.create(simple=None)
        obj = EmbeddedModelFieldModel.objects.get()
        self.assertIsNone(obj.simple)

    def test_pre_save(self):
        """Field.pre_save() is called on embedded model fields."""
        obj = EmbeddedModelFieldModel.objects.create(simple=EmbeddedModel())
        auto_now = self.truncate_ms(obj.simple.auto_now)
        auto_now_add = self.truncate_ms(obj.simple.auto_now_add)
        self.assertEqual(auto_now, auto_now_add)
        # save() updates auto_now but not auto_now_add.
        obj.save()
        self.assertEqual(self.truncate_ms(obj.simple.auto_now_add), auto_now_add)
        auto_now_two = obj.simple.auto_now
        self.assertGreater(auto_now_two, obj.simple.auto_now_add)
        # And again, save() updates auto_now but not auto_now_add.
        obj = EmbeddedModelFieldModel.objects.get()
        obj.save()
        self.assertEqual(obj.simple.auto_now_add, auto_now_add)
        self.assertGreater(obj.simple.auto_now, auto_now_two)

    def test_foreign_key_in_embedded_object(self):
        simple = EmbeddedModel(some_relation=Target.objects.create(index=1))
        obj = EmbeddedModelFieldModel.objects.create(simple=simple)
        simple = EmbeddedModelFieldModel.objects.get().simple
        self.assertNotIn("some_relation", simple.__dict__)
        self.assertIsInstance(simple.__dict__["some_relation_id"], type(obj.id))
        self.assertIsInstance(simple.some_relation, Target)

    def test_embedded_field_with_foreign_conversion(self):
        decimal = DecimalKey.objects.create(decimal=Decimal("1.5"))
        decimal_parent = DecimalParent.objects.create(child=decimal)
        EmbeddedModelFieldModel.objects.create(decimal_parent=decimal_parent)
