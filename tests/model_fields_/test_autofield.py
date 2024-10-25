from django.test import SimpleTestCase

from django_mongodb.fields import ObjectIdAutoField


class MethodTests(SimpleTestCase):
    def test_to_python(self):
        f = ObjectIdAutoField()
        self.assertEqual(f.to_python("1"), 1)
