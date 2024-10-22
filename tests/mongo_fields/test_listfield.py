from decimal import Decimal

from django.db import models
from django.db.models import Q
from django.test import TestCase

from django_mongodb.fields import ListField

from .models import (
    DecimalKey,
    DecimalsList,
    ListModel,
    Model,
    OrderedListModel,
    ReferenceList,
)


class IterableFieldsTests(TestCase):
    floats = [5.3, 2.6, 9.1, 1.58]
    names = ["Kakashi", "Naruto", "Sasuke", "Sakura"]
    unordered_ints = [4, 2, 6, 1]

    def setUp(self):
        self.objs = [
            ListModel.objects.create(
                integer=i, floating_point=self.floats[i], names=self.names[: i + 1]
            )
            for i in range(4)
        ]

    def test_startswith(self):
        self.assertEqual(
            {
                entity.pk: entity.names
                for entity in ListModel.objects.filter(names__startswith="Sa")
            },
            {
                3: ["Kakashi", "Naruto", "Sasuke"],
                4: ["Kakashi", "Naruto", "Sasuke", "Sakura"],
            },
        )

    def test_options(self):
        self.assertEqual(
            [
                entity.names_with_default
                for entity in ListModel.objects.filter(names__startswith="Sa")
            ],
            [[], []],
        )

        self.assertEqual(
            [entity.names_nullable for entity in ListModel.objects.filter(names__startswith="Sa")],
            [None, None],
        )

    def test_default_value(self):
        # Make sure default value is copied.
        ListModel().names_with_default.append(2)
        self.assertEqual(ListModel().names_with_default, [])

    def test_ordering(self):
        f = OrderedListModel._meta.fields[1]
        f.ordering.calls = 0

        # Ensure no ordering happens on assignment.
        obj = OrderedListModel()
        obj.ordered_ints = self.unordered_ints
        self.assertEqual(f.ordering.calls, 0)

        obj.save()
        self.assertEqual(OrderedListModel.objects.get().ordered_ints, sorted(self.unordered_ints))
        # Ordering should happen only once, i.e. the order function may
        # be called N times at most (N being the number of items in the
        # list).
        self.assertLessEqual(f.ordering.calls, len(self.unordered_ints))

    def test_gt(self):
        self.assertEqual(
            {entity.pk: entity.names for entity in ListModel.objects.filter(names__gt=["Naruto"])},
            {
                2: ["Kakashi", "Naruto"],
                3: ["Kakashi", "Naruto", "Sasuke"],
                4: ["Kakashi", "Naruto", "Sasuke", "Sakura"],
            },
        )

    def test_lt(self):
        self.assertEqual(
            {entity.pk: entity.names for entity in ListModel.objects.filter(names__lt="Naruto")},
            {
                1: ["Kakashi"],
                2: ["Kakashi", "Naruto"],
                3: ["Kakashi", "Naruto", "Sasuke"],
                4: ["Kakashi", "Naruto", "Sasuke", "Sakura"],
            },
        )

    def test_gte(self):
        self.assertEqual(
            {entity.pk: entity.names for entity in ListModel.objects.filter(names__gte="Sakura")},
            {
                3: ["Kakashi", "Naruto", "Sasuke"],
                4: ["Kakashi", "Naruto", "Sasuke", "Sakura"],
            },
        )

    def test_lte(self):
        self.assertEqual(
            {entity.pk: entity.names for entity in ListModel.objects.filter(names__lte="Kakashi")},
            {
                1: ["Kakashi"],
                2: ["Kakashi", "Naruto"],
                3: ["Kakashi", "Naruto", "Sasuke"],
                4: ["Kakashi", "Naruto", "Sasuke", "Sakura"],
            },
        )

    def test_equals(self):
        self.assertQuerySetEqual(
            ListModel.objects.filter(names=["Kakashi"]),
            [self.objs[0]],
        )

        # Test with additional pk filter (for DBs that have special pk
        # queries).
        query = ListModel.objects.filter(names=["Kakashi"])
        self.assertEqual(query.get(pk=query[0].pk).names, ["Kakashi"])

    def test_is_null(self):
        self.assertEqual(ListModel.objects.filter(names__isnull=True).count(), 0)

    def test_exclude(self):
        self.assertEqual(
            {
                entity.pk: entity.names
                for entity in ListModel.objects.all().exclude(names__lt="Sakura")
            },
            {
                3: ["Kakashi", "Naruto", "Sasuke"],
                4: ["Kakashi", "Naruto", "Sasuke", "Sakura"],
            },
        )

    def test_chained_filter(self):
        self.assertEqual(
            [
                entity.names
                for entity in ListModel.objects.filter(names="Sasuke").filter(names="Sakura")
            ],
            [
                ["Kakashi", "Naruto", "Sasuke", "Sakura"],
            ],
        )

        self.assertEqual(
            [
                entity.names
                for entity in ListModel.objects.filter(names__startswith="Sa").filter(
                    names="Sakura"
                )
            ],
            [["Kakashi", "Naruto", "Sasuke", "Sakura"]],
        )

        # Test across multiple columns. On app engine only one filter
        # is allowed to be an inequality filter.
        self.assertEqual(
            [
                entity.names
                for entity in ListModel.objects.filter(floating_point=9.1).filter(
                    names__startswith="Sa"
                )
            ],
            [
                ["Kakashi", "Naruto", "Sasuke"],
            ],
        )

    # @skip("GAE specific?")
    def test_Q_objects(self):
        self.assertEqual(
            [
                entity.names
                for entity in ListModel.objects.exclude(
                    Q(names__lt="Sakura") | Q(names__gte="Sasuke")
                )
            ],
            [["Kakashi", "Naruto", "Sasuke", "Sakura"]],
        )

    def test_list_with_foreign_keys(self):
        model1 = Model.objects.create()
        model2 = Model.objects.create()
        ReferenceList.objects.create(keys=[model1.pk, model2.pk])

        self.assertEqual(ReferenceList.objects.get().keys[0], model1.pk)
        self.assertEqual(ReferenceList.objects.filter(keys=[model1.pk, model2.pk]).count(), 1)

    def test_list_with_foreign_conversion(self):
        decimal = DecimalKey.objects.create(decimal=Decimal("1.5"))
        DecimalsList.objects.create(decimals=[decimal.pk])

    # @expectedFailure
    def test_nested_list(self):
        """
        Some back-ends expect lists to be strongly typed or not contain
        other lists (e.g. GAE), this limits how the ListField can be
        used (unless the back-end were to serialize all lists).
        """

        class UntypedListModel(models.Model):
            untyped_list = ListField()

        UntypedListModel.objects.create(untyped_list=[1, [2, 3]])
