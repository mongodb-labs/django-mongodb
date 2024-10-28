from django.test import TestCase

from .models import Author, Book


class MQLTests(TestCase):
    def test_all(self):
        with self.assertNumQueries(1) as ctx:
            list(Author.objects.all())
        query = ctx.captured_queries[0]["sql"]
        self.assertEqual(query, "db.queries__author.aggregate([{'$match': {'$expr': {}}}])")

    def test_join(self):
        with self.assertNumQueries(1) as ctx:
            list(Book.objects.filter(author__name="Bob"))
        query = ctx.captured_queries[0]["sql"]
        self.assertEqual(
            query,
            "db.queries__book.aggregate(["
            "{'$lookup': {'from': 'queries__author', "
            "'let': {'parent__field__0': {'$convert': {'input': '$author_id', 'to': 'string'}}}, "
            "'pipeline': [{'$match': {'$expr': {'$and': [{'$eq': ['$$parent__field__0', "
            "{'$convert': {'input': '$_id', 'to': 'string'}}]}]}}}], 'as': 'queries__author'}}, "
            "{'$unwind': '$queries__author'}, "
            "{'$match': {'$expr': {'$eq': ['$queries__author.name', 'Bob']}}}])",
        )
