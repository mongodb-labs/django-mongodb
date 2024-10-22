import time
from decimal import Decimal

from django.db import models
from django.test import TestCase

from .models import (
    Child,
    DecimalKey,
    DecimalParent,
    EmbeddedModel,
    EmbeddedModelFieldModel,
    OrderedListModel,
    Parent,
    Target,
)


class EmbeddedModelFieldTests(TestCase):
    def assertEqualDatetime(self, d1, d2):
        """Compares d1 and d2, ignoring microseconds."""
        self.assertEqual(d1.replace(microsecond=0), d2.replace(microsecond=0))

    def assertNotEqualDatetime(self, d1, d2):
        self.assertNotEqual(d1.replace(microsecond=0), d2.replace(microsecond=0))

    def _simple_instance(self):
        EmbeddedModelFieldModel.objects.create(simple=EmbeddedModel(someint="5"))
        return EmbeddedModelFieldModel.objects.get()

    def test_simple(self):
        instance = self._simple_instance()
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
        # Make sure field.pre_save is called for embedded objects.

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
        obj = EmbeddedModelFieldModel(simple_untyped=EmbeddedModel())
        self._test_pre_save(obj, lambda instance: instance.simple_untyped)

    def test_pre_save_in_list(self):
        obj = EmbeddedModelFieldModel(untyped_list=[EmbeddedModel()])
        self._test_pre_save(obj, lambda instance: instance.untyped_list[0])

    def _test_pre_save_in_dict(self):
        obj = EmbeddedModelFieldModel(untyped_dict={"a": EmbeddedModel()})
        self._test_pre_save(obj, lambda instance: instance.untyped_dict["a"])

    def test_pre_save_list(self):
        # Also make sure auto_now{,add} works for embedded object *lists*.
        EmbeddedModelFieldModel.objects.create(typed_list2=[EmbeddedModel()])
        instance = EmbeddedModelFieldModel.objects.get()

        auto_now = instance.typed_list2[0].auto_now
        auto_now_add = instance.typed_list2[0].auto_now_add
        self.assertNotEqual(auto_now, None)
        self.assertNotEqual(auto_now_add, None)

        instance.typed_list2.append(EmbeddedModel())
        instance.save()
        instance = EmbeddedModelFieldModel.objects.get()

        self.assertEqualDatetime(instance.typed_list2[0].auto_now_add, auto_now_add)
        self.assertGreater(instance.typed_list2[0].auto_now, auto_now)
        self.assertNotEqual(instance.typed_list2[1].auto_now, None)
        self.assertNotEqual(instance.typed_list2[1].auto_now_add, None)

    def test_error_messages(self):
        for kwargs, expected in (
            ({"simple": 42}, EmbeddedModel),
            ({"simple_untyped": 42}, models.Model),
            # ({"typed_list": [EmbeddedModel()]},), # SetModel),
        ):
            self.assertRaisesMessage(
                TypeError,
                "Expected instance of type %r" % expected,
                EmbeddedModelFieldModel(**kwargs).save,
            )

    def test_typed_listfield(self):
        EmbeddedModelFieldModel.objects.create(
            # typed_list=[SetModel(setfield=range(3)), SetModel(setfield=range(9))],
            ordered_list=[Target(index=i) for i in range(5, 0, -1)],
        )
        obj = EmbeddedModelFieldModel.objects.get()
        # self.assertIn(5, obj.typed_list[1].setfield)
        self.assertEqual([target.index for target in obj.ordered_list], list(range(1, 6)))

    def test_untyped_listfield(self):
        EmbeddedModelFieldModel.objects.create(
            untyped_list=[
                EmbeddedModel(someint=7),
                OrderedListModel(ordered_ints=list(range(5, 0, -1))),
                # SetModel(setfield=[1, 2, 2, 3]),
            ]
        )
        instances = EmbeddedModelFieldModel.objects.get().untyped_list
        for instance, cls in zip(
            instances,
            [EmbeddedModel, OrderedListModel],  # SetModel]
            strict=True,
        ):
            self.assertIsInstance(instance, cls)
        self.assertNotEqual(instances[0].auto_now, None)
        self.assertEqual(instances[1].ordered_ints, list(range(1, 6)))

    def _test_untyped_dict(self):
        EmbeddedModelFieldModel.objects.create(
            untyped_dict={
                # "a": SetModel(setfield=range(3)),
                #    "b": DictModel(dictfield={"a": 1, "b": 2}),
                #    "c": DictModel(dictfield={}, auto_now={"y": 1}),
            }
        )
        # data = EmbeddedModelFieldModel.objects.get().untyped_dict
        # self.assertIsInstance(data["a"], SetModel)
        # self.assertNotEqual(data["c"].auto_now["y"], None)

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

    def test_update(self):
        """
        QuerySet.update() can be used on an a subset of objects containing
        collections of embedded instances. Updated values are coerced according
        to the collection field.
        """
        child1 = Child.objects.create()
        child2 = Child.objects.create()
        parent = Parent.objects.create(
            pk=1,
            integer_list=[1],
            # integer_dict={"a": 2},
            embedded_list=[child1],
            # embedded_dict={"a": child2},
        )
        Parent.objects.filter(pk=1).update(
            integer_list=["3"],
            # integer_dict={"b": "3"},
            embedded_list=[child2],
            # embedded_dict={"b": child1},
        )
        parent = Parent.objects.get()
        self.assertEqual(parent.integer_list, [3])
        # self.assertEqual(parent.integer_dict, {"b": 3})
        self.assertEqual(parent.embedded_list, [child2])
        # self.assertEqual(parent.embedded_dict, {"b": child1})
