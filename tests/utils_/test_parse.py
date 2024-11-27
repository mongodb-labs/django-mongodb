from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

import django_mongodb

MONGODB_URI = "mongodb+srv://myDatabaseUser:D1fficultP%40ssw0rd@cluster0.example.mongodb.net/myDatabase?retryWrites=true&w=majority"


class MongoParseURITests(SimpleTestCase):
    """
    Test django_mongodb.parse(uri) function
    """

    @patch("dns.resolver.resolve")
    def test_parse(self, mock_resolver):
        srv_record = MagicMock()
        srv_record.target.to_text.return_value = "cluster0.example.mongodb.net"
        mock_resolver.return_value = [srv_record]
        settings_dict = django_mongodb.parse(MONGODB_URI)
        self.assertEqual(settings_dict["ENGINE"], "django_mongodb")
        self.assertEqual(settings_dict["NAME"], "myDatabase")
        self.assertEqual(settings_dict["HOST"], "mongodb+srv://cluster0.example.mongodb.net")
        self.assertEqual(settings_dict["USER"], "myDatabaseUser")
        self.assertEqual(settings_dict["PASSWORD"], "D1fficultP@ssw0rd")
        self.assertEqual(settings_dict["PORT"], None)
