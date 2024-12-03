from unittest.mock import MagicMock, patch

import pymongo
from django.test import SimpleTestCase

import django_mongodb

URI = "mongodb+srv://myDatabaseUser:D1fficultP%40ssw0rd@cluster0.example.mongodb.net/myDatabase?retryWrites=true&w=majority&tls=false"


class MongoParseURITests(SimpleTestCase):
    """
    Test django_mongodb.parse_uri(uri) function
    """

    def setUp(self):
        self.srv_record = MagicMock()
        self.srv_record.target.to_text.return_value = "cluster0.example.mongodb.net"
        self.patcher = patch("dns.resolver.resolve", return_value=[self.srv_record])
        self.mock_resolver = self.patcher.start()
        self.addCleanup(self.patcher.stop)

    @patch("dns.resolver.resolve")
    def test_uri(self, mock_resolver):
        settings_dict = django_mongodb.parse_uri(
            "mongodb://cluster0.example.mongodb.net/myDatabase"
        )
        self.assertEqual(settings_dict["ENGINE"], "django_mongodb")
        self.assertEqual(settings_dict["NAME"], "myDatabase")
        self.assertEqual(settings_dict["HOST"], "cluster0.example.mongodb.net")

    @patch("dns.resolver.resolve")
    def test_srv_uri_with_options(self, mock_resolver):
        settings_dict = django_mongodb.parse_uri(URI)
        self.assertEqual(settings_dict["ENGINE"], "django_mongodb")
        self.assertEqual(settings_dict["NAME"], "myDatabase")
        self.assertEqual(settings_dict["HOST"], "mongodb+srv://cluster0.example.mongodb.net")
        self.assertEqual(settings_dict["USER"], "myDatabaseUser")
        self.assertEqual(settings_dict["PASSWORD"], "D1fficultP@ssw0rd")
        self.assertEqual(settings_dict["PORT"], None)
        self.assertEqual(
            settings_dict["OPTIONS"], {"retryWrites": True, "w": "majority", "tls": False}
        )

    def test_localhost(self):
        settings_dict = django_mongodb.parse_uri("mongodb://localhost/myDatabase")
        self.assertEqual(settings_dict["ENGINE"], "django_mongodb")
        self.assertEqual(settings_dict["NAME"], "myDatabase")
        self.assertEqual(settings_dict["HOST"], "localhost")

    def test_localhost_bad_credentials(self):
        with self.assertRaises(pymongo.errors.InvalidURI):
            django_mongodb.parse_uri("mongodb://:@localhost/myDatabase")

    @patch("dns.resolver.resolve")
    def test_engine_kwarg(self, mock_resolver):
        settings_dict = django_mongodb.parse_uri(URI, engine="some_other_engine")
        self.assertEqual(settings_dict["ENGINE"], "some_other_engine")

    @patch("dns.resolver.resolve")
    def test_conn_max_age_kwarg(self, mock_resolver):
        settings_dict = django_mongodb.parse_uri(URI, conn_max_age=600)
        self.assertEqual(settings_dict["CONN_MAX_AGE"], 600)

    @patch("dns.resolver.resolve")
    def test_conn_health_checks_kwarg(self, mock_resolver):
        settings_dict = django_mongodb.parse_uri(URI, conn_health_checks=True)
        self.assertEqual(settings_dict["CONN_HEALTH_CHECKS"], True)

    @patch("dns.resolver.resolve")
    def test_test_kwarg(self, mock_resolver):
        settings_dict = django_mongodb.parse_uri(URI, test={"NAME": "test_db"})
        self.assertEqual(settings_dict["TEST"]["NAME"], "test_db")

    @patch("dns.resolver.resolve")
    def test_uri_no_prefix(self, mock_resolver):
        with self.assertRaises(pymongo.errors.InvalidURI):
            django_mongodb.parse_uri("cluster0.example.mongodb.net/myDatabase")
