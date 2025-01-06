from django.test import SimpleTestCase

from django_mongodb_backend.fields import ObjectIdAutoField


class MethodTests(SimpleTestCase):
    def test_deconstruct(self):
        field = ObjectIdAutoField()
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django_mongodb_backend.fields.ObjectIdAutoField")
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"primary_key": True})

    def test_get_internal_type(self):
        f = ObjectIdAutoField()
        self.assertEqual(f.get_internal_type(), "ObjectIdAutoField")

    def test_to_python(self):
        f = ObjectIdAutoField()
        self.assertEqual(f.to_python("1"), 1)
