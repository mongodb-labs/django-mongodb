from bson import ObjectId
from django.core import exceptions
from django.test import SimpleTestCase

from django_mongodb.fields import ObjectIdField


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
                with self.assertRaisesMessage(exceptions.ValidationError, msg):
                    f.to_python(invalid_value)

    def test_get_prep_value_string(self):
        value = "1" * 24
        self.assertEqual(ObjectIdField().get_prep_value(value), ObjectId(value))

    def test_get_prep_value_objectid(self):
        value = ObjectId("1" * 24)
        self.assertEqual(ObjectIdField().get_prep_value(value), value)

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
