from bson import ObjectId
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase

from django_mongodb.fields import ObjectIdField

from .models import NullableObjectIdModel, ObjectIdModel, PrimaryKeyObjectIdModel


class MethodTests(SimpleTestCase):
    def test_deconstruct(self):
        field = ObjectIdField()
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django_mongodb.fields.ObjectIdField")
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {})

    def test_get_internal_type(self):
        f = ObjectIdField()
        self.assertEqual(f.get_internal_type(), "ObjectIdField")

    def test_to_python_string(self):
        value = "1" * 24
        self.assertEqual(ObjectIdField().to_python(value), ObjectId(value))

    def test_to_python_objectid(self):
        value = ObjectId("1" * 24)
        self.assertEqual(ObjectIdField().to_python(value), value)

    def test_to_python_null(self):
        self.assertIsNone(ObjectIdField().to_python(None))

    def test_to_python_invalid_value(self):
        f = ObjectIdField()
        for invalid_value in ["None", {}, [], 123]:
            with self.subTest(invalid_value=invalid_value):
                msg = f"['“{invalid_value}” value must be an Object Id.']"
                with self.assertRaisesMessage(ValidationError, msg):
                    f.to_python(invalid_value)

    def test_get_prep_value_string(self):
        value = "1" * 24
        self.assertEqual(ObjectIdField().get_prep_value(value), ObjectId(value))

    def test_get_prep_value_objectid(self):
        value = ObjectId("1" * 24)
        self.assertEqual(ObjectIdField().get_prep_value(value), value)

    def test_get_prep_value_empty(self):
        # This is necessary to allow an empty ObjectIdField to be saved in
        # forms, unless we add an ObjectId form field to do the conversion (see
        # UUIDField for an example).
        self.assertIsNone(ObjectIdField().get_prep_value(""))

    def test_get_prep_value_null(self):
        self.assertIsNone(ObjectIdField().get_prep_value(None))

    def test_get_prep_value_invalid_values(self):
        f = ObjectIdField()
        f.name = "test"
        for invalid_value in ["None", {}, [], 123]:
            with self.subTest(invalid_value=invalid_value):
                msg = f"Field 'test' expected an ObjectId but got {invalid_value!r}."
                with self.assertRaisesMessage(ValueError, msg):
                    f.get_prep_value(invalid_value)


class SaveLoadTests(TestCase):
    def test_objectid_instance(self):
        instance = ObjectIdModel.objects.create(field=ObjectId())
        loaded = ObjectIdModel.objects.get()
        self.assertEqual(loaded.field, instance.field)

    def test_str_instance(self):
        ObjectIdModel.objects.create(field="6754ed8e584bc9ceaae3c072")
        loaded = ObjectIdModel.objects.get()
        self.assertEqual(loaded.field, ObjectId("6754ed8e584bc9ceaae3c072"))

    def test_null_handling(self):
        NullableObjectIdModel.objects.create(field=None)
        loaded = NullableObjectIdModel.objects.get()
        self.assertIsNone(loaded.field)

    def test_pk_validated(self):
        # See https://code.djangoproject.com/ticket/24859
        with self.assertRaisesMessage(TypeError, "must be an Object Id."):
            PrimaryKeyObjectIdModel.objects.get(pk={})

        with self.assertRaisesMessage(TypeError, "must be an Object Id."):
            PrimaryKeyObjectIdModel.objects.get(pk=[])

    def test_wrong_value(self):
        # Copied from  UUID tests. Raises ValueError, might be okay.
        with self.assertRaisesMessage(ValidationError, "must be an Object Id."):
            ObjectIdModel.objects.get(field="not-a-objectid")

        with self.assertRaisesMessage(ValidationError, "must be an Object Id."):
            ObjectIdModel.objects.create(field="not-a-objectid")
