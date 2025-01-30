from django.db import NotSupportedError
from django.test import SimpleTestCase

from .models import Embed


class TestMethods(SimpleTestCase):
    def test_save(self):
        e = Embed()
        with self.assertRaisesMessage(NotSupportedError, "EmbeddedModels cannot be saved."):
            e.save()

    def test_delete(self):
        e = Embed()
        with self.assertRaisesMessage(NotSupportedError, "EmbeddedModels cannot be deleted."):
            e.delete()


class TestManagerMethods(SimpleTestCase):
    def test_all(self):
        with self.assertRaisesMessage(NotSupportedError, "EmbeddedModels cannot be queried."):
            Embed.objects.all()

    def test_get(self):
        with self.assertRaisesMessage(NotSupportedError, "EmbeddedModels cannot be queried."):
            Embed.objects.get(foo="bar")

    def test_filter(self):
        with self.assertRaisesMessage(NotSupportedError, "EmbeddedModels cannot be queried."):
            Embed.objects.filter(foo="bar")

    def test_create(self):
        with self.assertRaisesMessage(NotSupportedError, "EmbeddedModels cannot be created."):
            Embed.objects.create(foo="bar")

    def test_update(self):
        with self.assertRaisesMessage(NotSupportedError, "EmbeddedModels cannot be updated."):
            Embed.objects.update(foo="bar")

    def test_delete(self):
        with self.assertRaisesMessage(NotSupportedError, "EmbeddedModels cannot be deleted."):
            Embed.objects.delete()

    def test_get_or_create(self):
        msg = "'EmbeddedModelManager' object has no attribute 'get_or_create'"
        with self.assertRaisesMessage(AttributeError, msg):
            Embed.objects.get_or_create()
