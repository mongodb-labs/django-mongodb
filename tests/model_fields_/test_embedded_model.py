import time
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
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
        field = EmbeddedModelField()
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django_mongodb.fields.EmbeddedModelField")
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {})

    def test_deconstruct_with_model(self):
        field = EmbeddedModelField("EmbeddedModel", null=True)
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django_mongodb.fields.EmbeddedModelField")
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"embedded_model": "EmbeddedModel", "null": True})

    def test_validate(self):
        instance = EmbeddedModelFieldModel(simple=EmbeddedModel(someint=None))
        # This isn't quite right because "someint" is the field that's non-null.
        msg = "{'simple': ['This field cannot be null.']}"
        with self.assertRaisesMessage(ValidationError, msg):
            instance.full_clean()


class QueryingTests(TestCase):
    def assertEqualDatetime(self, d1, d2):
        """Compares d1 and d2, ignoring microseconds."""
        self.assertEqual(d1.replace(microsecond=0), d2.replace(microsecond=0))

    def assertNotEqualDatetime(self, d1, d2):
        self.assertNotEqual(d1.replace(microsecond=0), d2.replace(microsecond=0))

    def test_save_load(self):
        EmbeddedModelFieldModel.objects.create(simple=EmbeddedModel(someint="5"))
        instance = EmbeddedModelFieldModel.objects.get()
        self.assertIsInstance(instance.simple, EmbeddedModel)
        # Make sure get_prep_value is called.
        self.assertEqual(instance.simple.someint, 5)
        # Primary keys should not be populated...
        self.assertEqual(instance.simple.id, None)
        # ... unless set explicitly.
        instance.simple.id = instance.id
        instance.save()
        instance = EmbeddedModelFieldModel.objects.get()
        self.assertEqual(instance.simple.id, instance.id)

    def test_save_load_untyped(self):
        EmbeddedModelFieldModel.objects.create(simple=EmbeddedModel(someint="5"))
        instance = EmbeddedModelFieldModel.objects.get()
        self.assertIsInstance(instance.simple, EmbeddedModel)
        # Make sure get_prep_value is called.
        self.assertEqual(instance.simple.someint, 5)
        # Primary keys should not be populated...
        self.assertEqual(instance.simple.id, None)
        # ... unless set explicitly.
        instance.simple.id = instance.id
        instance.save()
        instance = EmbeddedModelFieldModel.objects.get()
        self.assertEqual(instance.simple.id, instance.id)

    def _test_pre_save(self, instance, get_field):
        # Field.pre_save() is called on embedded model fields.

        instance.save()
        auto_now = get_field(instance).auto_now
        auto_now_add = get_field(instance).auto_now_add
        self.assertNotEqual(auto_now, None)
        self.assertNotEqual(auto_now_add, None)

        time.sleep(1)  # FIXME
        instance.save()
        self.assertNotEqualDatetime(get_field(instance).auto_now, get_field(instance).auto_now_add)

        instance = EmbeddedModelFieldModel.objects.get()
        instance.save()
        # auto_now_add shouldn't have changed now, but auto_now should.
        self.assertEqualDatetime(get_field(instance).auto_now_add, auto_now_add)
        self.assertGreater(get_field(instance).auto_now, auto_now)

    def test_pre_save(self):
        obj = EmbeddedModelFieldModel(simple=EmbeddedModel())
        self._test_pre_save(obj, lambda instance: instance.simple)

    def test_pre_save_untyped(self):
        obj = EmbeddedModelFieldModel(untyped=EmbeddedModel())
        self._test_pre_save(obj, lambda instance: instance.untyped)

    def test_error_messages(self):
        for model_kwargs, expected in (
            ({"simple": 42}, EmbeddedModel),
            ({"untyped": 42}, models.Model),
        ):
            msg = "Expected instance of type %r" % expected
            with self.assertRaisesMessage(TypeError, msg):
                EmbeddedModelFieldModel(**model_kwargs).save()

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
